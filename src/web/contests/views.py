import copy
import itertools
import operator
import re
import collections
import datetime

from django.contrib import messages
from django.core import urlresolvers
from django.db import transaction
from django.db.models.query_utils import Q
from django.http.response import Http404, HttpResponseNotFound, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.conf import settings

from drapo.common import respond_as_attachment
from drapo.uploads import save_uploaded_file
from users.decorators import login_required, staff_required
import users.models as users_models
from . import models
from . import forms
import teams.models as teams_models
import taskbased.categories.models as categories_models
import taskbased.tasks.models as tasks_models
import taskbased.tasks.forms as tasks_forms


def _groupby(iterable, keyfunc):
    result = collections.defaultdict(list)
    for item in iterable:
        key = keyfunc(item)
        result[key].append(item)

    return result


def is_manual_task_opening_available_in_contest(contest):
    return contest.tasks_opening_policies.instance_of(tasks_models.ManualTasksOpeningPolicy).exists()


def contests_list(request):
    contests = models.Contest.objects.filter(is_visible_in_list=True).order_by('-start_time')

    if request.user.is_authenticated():
        for contest in contests:
            contest.is_current_user_participating = contest.is_user_participating(request.user)

    return render(request, 'contests/list.html', {
        'contests': contests
    })


@login_required
@transaction.atomic
def join(request, contest_id):
    contest = get_object_or_404(models.Contest, pk=contest_id, is_visible_in_list=True)

    form = None
    if request.method == 'POST':
        if contest.is_user_participating(request.user):
            messages.info(request, 'You are already participating in this contest')
            return redirect(contest)

        if contest.registration_type == models.ContestRegistrationType.Closed:
            messages.error(request, 'Registration for this contest is closed. Only administrators can register tou')
            return redirect(contest)

        if not contest.can_register_now():
            messages.error(request, 'Registration for this contest is finished')
            return redirect(contest)

        is_participant_approved = contest.registration_type == models.ContestRegistrationType.Open

        if contest.participation_mode == models.ContestParticipationMode.Individual:
            models.IndividualParticipant(
                contest=contest,
                user=request.user,
                is_approved=is_participant_approved,
            ).save()
            messages.success(request, 'Welcome to ' + contest.name + '!')
            return redirect(contest)

        if contest.participation_mode == models.ContestParticipationMode.Team:
            form = forms.ChooseTeamForm(request.user, data=request.POST)
            if form.is_valid():
                team_id = form.cleaned_data['team']
                team = teams_models.Team.objects.get(pk=team_id)
                models.TeamParticipant(
                    contest=contest,
                    team=team,
                    is_approved=is_participant_approved,
                ).save()
                messages.success(request, 'Welcome to ' + contest.name + ', ' + team.name + '!')
                return redirect(contest)

    if contest.participation_mode == models.ContestParticipationMode.Team:
        if form is None:
            form = forms.ChooseTeamForm(request.user)
        user_teams = list(request.user.teams.all())
        invite_hash_form = forms.JoinViaInviteHashForm()

        return render(request, 'contests/join_team.html', {
            'current_contest': contest,

            'contest': contest,
            'form': form,
            'user_teams': user_teams,
            'invite_hash_form': invite_hash_form
        })

    messages.warning(request, 'Sorry, you can not join this contest')

    return redirect(contest)


def contest(request, contest_id):
    contest = get_object_or_404(models.Contest, pk=contest_id)

    if not contest.is_visible_in_list:
        has_access = (request.user.is_authenticated() and
                      (request.user.is_staff or contest.is_user_participating(request.user)))
        if not has_access:
            return HttpResponseNotFound()

    participants = contest.participants.filter(is_approved=True)

    news = contest.news.order_by('-publish_time')
    if not request.user.is_staff:
        news = news.filter(is_published=True)

    return render(request, 'contests/contest.html', {
        'current_contest': contest,

        'contest': contest,
        'news': news,
        'participants': participants,
    })


def tasks(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if not contest.is_visible_in_list and not request.user.is_staff:
        return HttpResponseNotFound()

    if not contest.is_started() and not request.user.is_staff:
        messages.error(request, '%s is not started yet' % contest.name)
        return redirect(contest)

    solved_tasks_ids = {}
    if request.user.is_authenticated():
        participant = contest.get_participant_for_user(request.user)
        solved_tasks_ids = contest.get_tasks_solved_by_participant(participant)
    else:
        participant = None

    # Iterate all policies, collect opened tasks
    opened_tasks_ids = set(
        itertools.chain.from_iterable(
            policy.get_open_tasks(participant) for policy in contest.tasks_opening_policies.all()
        )
    )

    if contest.tasks_grouping == models.TasksGroping.OneByOne:
        tasks = contest.tasks
        return render(request, 'contests/tasks_one_by_one.html', {
            'current_contest': contest,

            'contest': contest,
            'tasks': tasks,
            'solved_tasks_ids': solved_tasks_ids,
            'opened_tasks_ids': opened_tasks_ids,
        })
    if contest.tasks_grouping == models.TasksGroping.ByCategories:
        categories = contest.categories
        return render(request, 'contests/tasks_by_categories.html', {
            'current_contest': contest,

            'contest': contest,
            'categories': categories,
            'solved_tasks_ids': solved_tasks_ids,
            'opened_tasks_ids': opened_tasks_ids,
        })


def scoreboard(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if not contest.is_visible_in_list and not request.user.is_staff:
        return HttpResponseNotFound()

    participants = list(contest.participants.filter(is_visible_in_scoreboard=True))


    attempts_by_participant = _groupby(contest.attempts.all(), operator.attrgetter('participant_id'))
    attempts_by_participant = collections.defaultdict(list, attempts_by_participant)

    attempts_by_participant_and_task = {
        p.id: collections.defaultdict(
            list,
            _groupby(attempts_by_participant[p.id], operator.attrgetter('task_id'))
        )
        for p in participants
        }

    # Stores first success attempt for each pair (participant, task) or None if there is no success tries
    first_success_attempt_by_participant_and_task = {
        p.id: collections.defaultdict(
            lambda: None,
            {
                # For each task_id filter only correct attempts and select first created
                task_id: min(
                    filter(operator.attrgetter('is_correct'), attempts),
                    key=lambda a: a.created_at,
                    default=None
                )
                for task_id, attempts in attempts_by_participant_and_task[p.id].items()
                }
        )
        for p in participants
        }

    max_scored_attempt_by_participant_and_task = {
        p.id: collections.defaultdict(
            None,
            {
                # For each task_id filter only checked attempts and select one with max score
                task_id: max(
                    filter(operator.attrgetter('is_checked'), attempts),
                    key=lambda a: a.score,
                    default=None
                )
                for task_id, attempts in attempts_by_participant_and_task[p.id].items()
                }
        )
        for p in participants
        }

    scores_by_participant = {
        p.id: sum(a.score for a in max_scored_attempt_by_participant_and_task[p.id].values() if a is not None)
        for p in participants
        }

    last_success_time_by_participant = {
        p.id: max((a.created_at for a in attempts_by_participant[p.id] if a.is_correct), default=0)
        for p in participants
        }

    ordered_participants = sorted(participants,
                                  key=lambda p: (
                                      p.is_disqualified,  # First, show not-disqualified participants
                                      -scores_by_participant[p.id],  # ordered by scores
                                      last_success_time_by_participant[p.id]  # and by last success time
                                  ))

    tasks = categories = None
    if contest.tasks_grouping == models.TasksGroping.OneByOne:
        tasks = contest.tasks
        with_categories = False
    elif contest.tasks_grouping == models.TasksGroping.ByCategories:
        categories = contest.categories
        with_categories = True
    else:
        raise ValueError('Invalid tasks grouping mode')

    return render(request, 'contests/scoreboard.html', {
        'current_contest': contest,

        'contest': contest,
        'with_categories': with_categories,
        'tasks': tasks,
        'categories': categories,
        'participants': ordered_participants,
        'scores_by_participant': scores_by_participant,
        'max_scored_attempt_by_participant_and_task': max_scored_attempt_by_participant_and_task,
        'first_success_attempt_by_participant_and_task': first_success_attempt_by_participant_and_task
    })


def get_count_attempts_in_last_minute(contest, participant):
    minute_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)
    return tasks_models.Attempt.objects.filter(
        contest=contest,
        participant=participant,
        created_at__gte=minute_ago
    ).count()


def is_task_open(contest, task, participant):
    return any(task.id in policy.get_open_tasks(participant) for policy in contest.tasks_opening_policies.all())


def task(request, contest_id, task_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if not contest.is_visible_in_list and not request.user.is_staff:
        return HttpResponseNotFound()

    task = get_object_or_404(tasks_models.Task, pk=task_id)
    if not contest.has_task(task):
        return HttpResponseNotFound()

    if not contest.is_started() and not request.user.is_staff:
        return HttpResponseForbidden('Contest is not started')

    participant = contest.get_participant_for_user(request.user)

    if not is_task_open(contest, task, participant) and not request.user.is_staff:
        return HttpResponseForbidden('Task is closed')

    if request.method == 'POST' and request.user.is_authenticated():
        form = tasks_forms.AttemptForm(data=request.POST)

        if participant is None:
            messages.warning(request, 'You are not registered to the contest')
        elif participant.is_disqualified:
            messages.error(request, 'You are disqualified from the contest')
        elif get_count_attempts_in_last_minute(contest, participant) >= settings.DRAPO_MAX_TRIES_IN_MINUTE:
            messages.error(request, 'Too fast, try later')
        elif contest.is_finished():
            messages.error(request, 'Contest is finished! You are too late, sorry')
        elif form.is_valid():
            answer = form.cleaned_data['answer']
            attempt = tasks_models.Attempt(
                contest=contest,
                task=task,
                participant=contest.get_participant_for_user(request.user),
                author=request.user,
                answer=answer
            )
            attempt.save()

            attempt.try_to_check()

            if not attempt.is_checked:
                messages.info(request, 'We will check you answer, thank you')
            elif attempt.is_correct:
                messages.success(request, 'Yeah! Correct answer!')
            else:
                messages.error(request, 'Wrong answer, sorry')

            return redirect(urlresolvers.reverse('contests:task', args=[contest.id, task.id]))
    else:
        form = tasks_forms.AttemptForm()

    statement_generator = task.statement_generator
    if request.user.is_anonymous() and not statement_generator.is_available_for_anonymous():
        messages.error(request, 'This task is not available for guests. Please sign in')
        return redirect(urlresolvers.reverse('contests:tasks', args=[contest.id]))

    statement = statement_generator.generate({
        'user': request.user,
        'participant': participant
    })

    # Files can be in statement or in task for this participant
    files = statement.files + list(task.files.filter(Q(participant__isnull=True) | Q(participant=participant)))

    participant_score = max(task.attempts
                            .filter(contest=contest_id, participant=participant, is_checked=True)
                            .values_list('score', flat=True),
                            default=None
                            )

    return render(request, 'contests/task.html', {
        'current_contest': contest,

        'contest': contest,
        'task': task,
        'statement': statement,
        'files': files,
        'attempt_form': form,
        'participant': participant,
        'participant_score': participant_score,
    })


@staff_required
def add_category(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if contest.tasks_grouping != models.TasksGroping.ByCategories:
        return HttpResponseNotFound()

    if request.method == 'POST':
        form = forms.CategoryForm(data=request.POST)
        if form.is_valid():
            category = categories_models.Category(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description']
            )
            with transaction.atomic():
                category.save()

                contest.categories_list.categories.add(category)
                contest.save()
            return redirect(urlresolvers.reverse('contests:tasks', args=[contest.id]))
    else:
        form = forms.CategoryForm()

    return render(request, 'contests/create_category.html', {
        'current_contest': contest,

        'contest': contest,
        'form': form,
    })


@staff_required
def edit_category(request, contest_id, category_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if contest.tasks_grouping != models.TasksGroping.ByCategories:
        return HttpResponseNotFound()
    category = get_object_or_404(categories_models.Category, pk=category_id)
    if not contest.categories_list.categories.filter(id=category.id).exists():
        return HttpResponseNotFound()

    if request.method == 'POST':
        form = forms.CategoryForm(data=request.POST)
        if form.is_valid():
            new_category = categories_models.Category(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description']
            )
            new_category.id = category.id
            new_category.save()
            return redirect(urlresolvers.reverse('contests:tasks', args=[contest.id]))
    else:
        form = forms.CategoryForm(initial=category.__dict__)

    return render(request, "contests/edit_category.html", {
        'current_contest': contest,

        'contest': contest,
        'category': category,
        'form': form,
    })


@staff_required
@require_POST
def delete_category(request, contest_id, category_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if contest.tasks_grouping != models.TasksGroping.ByCategories:
        return HttpResponseNotFound()
    category = get_object_or_404(categories_models.Category, pk=category_id)
    if not contest.categories_list.categories.filter(id=category.id).exists():
        return HttpResponseNotFound()

    contest.categories_list.categories.remove(category)
    contest.categories_list.save()

    return redirect(urlresolvers.reverse('contests:tasks', args=[contest.id]))


@staff_required
def attempts(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)

    attempts = contest.attempts.order_by('-created_at').select_related(
        'task', 'participant', 'participant__teamparticipant', 'participant__individualparticipant', 'author'
    )

    form = forms.AttemptsSearchForm(data=request.GET)
    if form.is_valid():
        pattern = form.cleaned_data['pattern']
        if pattern != '':
            attempts = attempts.filter(Q(task__name__icontains=pattern) |
                                       Q(author__username__icontains=pattern) |
                                       Q(author__first_name__icontains=pattern) |
                                       Q(author__last_name__icontains=pattern) |
                                       Q(participant__teamparticipant__team__name__icontains=pattern) |
                                       Q(answer__icontains=pattern))

    return render(request, 'contests/attempts.html', {
        'current_contest': contest,

        'contest': contest,
        'pattern': pattern,
        'attempts': attempts,
        'form': form,
    })


@staff_required
def attempt(request, contest_id, attempt_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    attempt = get_object_or_404(tasks_models.Attempt, pk=attempt_id)

    if attempt.contest_id != contest.id:
        return HttpResponseNotFound()

    if request.method == 'POST':
        form = tasks_forms.EditAttemptForm(attempt, data=request.POST)
        if form.is_valid():
            new_attempt = tasks_models.Attempt(
                contest=contest,
                task=attempt.task,
                author=attempt.author,
                participant=attempt.participant,
                created_at=attempt.created_at,
                is_correct=form.cleaned_data['score'] == attempt.task.max_score,
                **form.cleaned_data
            )
            new_attempt.id = attempt.id
            new_attempt.save()

            messages.success(request, 'Saved!')
            return redirect(urlresolvers.reverse('contests:attempts', args=[contest.id]))
    else:
        form = tasks_forms.EditAttemptForm(attempt)

    return render(request, 'contests/edit_attempt.html', {
        'current_contest': contest,

        'contest': contest,
        'attempt': attempt,
        'form': form,
    })


@staff_required
def create(request):
    if request.method == 'POST':
        form = forms.TaskBasedContestForm(data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                contest_data = copy.copy(form.cleaned_data)
                del contest_data['by_categories_tasks_opening_policy']
                del contest_data['manual_tasks_opening_policy']

                contest = models.TaskBasedContest(
                    **contest_data
                )
                contest.save()
                if contest.tasks_grouping == models.TasksGroping.ByCategories:
                    categories_models.ContestCategories(contest=contest).save()
                elif contest.tasks_grouping == models.TasksGroping.OneByOne:
                    tasks_models.ContestTasks(contest=contest).save()

                if form.cleaned_data['by_categories_tasks_opening_policy'] != '-':
                    tasks_models.ByCategoriesTasksOpeningPolicy(
                        contest=contest,
                        opens_for_all_participants=form.cleaned_data['by_categories_tasks_opening_policy'] == 'E'
                    ).save()

                if form.cleaned_data['manual_tasks_opening_policy']:
                    tasks_models.ManualTasksOpeningPolicy(
                        contest=contest
                    ).save()
            messages.success(request, 'Contest «%s» created' % contest.name)
            return redirect(contest)
    else:
        form = forms.TaskBasedContestForm()

    return render(request, 'contests/create.html', {
        'form': form
    })


@staff_required
def participants(request, contest_id):
    contest = get_object_or_404(models.Contest, pk=contest_id)

    participants = contest.participants.all()

    manual_register_participant_form = forms.ManualRegisterParticipant()

    return render(request, 'contests/participants.html', {
        'current_contest': contest,

        'contest': contest,
        'participants': participants,
        'manual_register_participant_form': manual_register_participant_form,
    })


class CannotAddParticipant(Exception):
    pass


@staff_required
def add_participant(request, contest_id):
    contest = get_object_or_404(models.Contest, pk=contest_id)

    if request.method == 'POST':
        form = forms.ManualRegisterParticipant(data=request.POST)

        try:
            if not form.is_valid():
                raise CannotAddParticipant('Fill the link field')

            link = form.cleaned_data['participant_link']
            user_re = re.compile(r'.+/users/(\d+)/?$')
            team_re = re.compile(r'.+/teams/(\d+)/?$')

            if contest.participation_mode == models.ContestParticipationMode.Individual:
                match = user_re.match(link)

                if match is None:
                    raise CannotAddParticipant('It\'s not like the link to the user (should be /users/123/)')

                user_id = int(match.group(1))
                # Limit for database query: i.e. sqlite can't operate with large integers
                if user_id > 1000000:
                    raise CannotAddParticipant('It\'s not like the link to the user (should be /users/123/)')

                try:
                    user = users_models.User.objects.get(pk=match.group(1))
                except users_models.User.DoesNotExist:
                    raise CannotAddParticipant('It\'s not like the link to the user (should be /users/123/)')

                with transaction.atomic():
                    if contest.is_user_participating(user):
                        raise CannotAddParticipant('This user is already participating in this contest')

                    models.IndividualParticipant(contest=contest, user=user).save()
                    messages.success(request, 'Added %s to the contest' % (user.get_full_name(),))

            if contest.participation_mode == models.ContestParticipationMode.Team:
                match = team_re.match(link)

                if match is None:
                    raise CannotAddParticipant('It\'s not like the link to the team (should be /teams/123/)')

                team_id = int(match.group(1))
                # Limit for database query: i.e. sqlite can't operate with large integers
                if team_id > 1000000:
                    raise CannotAddParticipant('It\'s not like the link to the team (should be /teams/123/)')

                try:
                    team = teams_models.Team.objects.get(pk=match.group(1))
                except teams_models.Team.DoesNotExist:
                    raise CannotAddParticipant('It\'s not like the link to the team (should be /teams/123/)')

                with transaction.atomic():
                    if contest.participants.filter(team__id=team.id).exists():
                        raise CannotAddParticipant('This team is already participating in this contest')

                    models.IndividualParticipant(contest=contest, team=team).save()
                    messages.success(request, 'Added %s to the contest' % (team.name,))

        except CannotAddParticipant as e:
            messages.error(request, str(e))

    return redirect(urlresolvers.reverse('contests:participants', args=[contest.id]))


@staff_required
@require_POST
def change_participant_status(request, contest_id, participant_id):
    contest = get_object_or_404(models.Contest, pk=contest_id)

    participant = get_object_or_404(models.AbstractParticipant, pk=participant_id, contest_id=contest_id)

    parameter = request.POST['parameter']
    value = request.POST['value'] == 'true'

    if parameter not in ('is_approved', 'is_disqualified', 'is_visible_in_scoreboard'):
        return HttpResponseNotFound()

    setattr(participant, parameter, value)
    participant.save()

    return redirect(urlresolvers.reverse('contests:participants', args=[contest.id]))


def add_task_to_contest(contest, category, task):
    if category is not None:
        category.tasks.add(task)
        category.save()
    else:
        contest.tasks_list.tasks.add(task)
        contest.tasks_list.save()


def add_task_to_contest_view(request, contest, category=None):
    if request.method == 'POST':
        form = forms.CreateTaskForm(data=request.POST, files=request.FILES)
        create_text_checker_form = forms.CreateTextCheckerForm(data=request.POST)
        create_regexp_checker_form = forms.CreateRegExpCheckerForm(data=request.POST)
        if form.is_valid():
            checker_type = form.cleaned_data['checker_type']
            if checker_type == 'text':
                checker_form = create_text_checker_form
            elif checker_type == 'regexp':
                checker_form = create_regexp_checker_form
            else:
                checker_form = None

            if checker_form is not None and checker_form.is_valid():
                checker = checker_form.get_checker()
                statement_generator = tasks_models.TextStatementGenerator(
                    title=form.cleaned_data['statement_title'],
                    template=form.cleaned_data['statement_template'],
                )

                with transaction.atomic():
                    checker.save()
                    statement_generator.save()
                    task = tasks_models.Task(
                        name=form.cleaned_data['name'],
                        max_score=form.cleaned_data['max_score'],
                        statement_generator=statement_generator,
                        checker=checker,
                    )
                    task.save()

                    add_task_to_contest(contest, category, task)

                    for uploaded_file in request.FILES.getlist('statement_files'):
                        task_file_dir = tasks_models.TaskFile.generate_directory_name(task, None)
                        task_file_name = save_uploaded_file(uploaded_file, task_file_dir)

                        task_file = tasks_models.TaskFile(
                            task=task,
                            name=uploaded_file.name[:1000],
                            path=task_file_name,
                            content_type=uploaded_file.content_type[:100]
                        )
                        task_file.save()

                messages.success(request, 'Task %s successfully created' % task.name)

                return redirect(urlresolvers.reverse('contests:tasks', args=[contest.id]))
    else:
        form = forms.CreateTaskForm()
        create_text_checker_form = forms.CreateTextCheckerForm()
        create_regexp_checker_form = forms.CreateRegExpCheckerForm()

    return render(request, 'contests/create_task.html', {
        'current_contest': contest,

        'contest': contest,
        'category': category,
        'form': form,
        'create_text_checker_form': create_text_checker_form,
        'create_regexp_checker_form': create_regexp_checker_form,
    })


@staff_required
def add_task_to_category(request, contest_id, category_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    category = get_object_or_404(categories_models.Category, pk=category_id, contestcategories__contest_id=contest_id)

    if contest.tasks_grouping != models.TasksGroping.ByCategories:
        return HttpResponseNotFound()

    return add_task_to_contest_view(request, contest, category)


@staff_required
def add_task(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if contest.tasks_grouping != models.TasksGroping.OneByOne:
        return HttpResponseNotFound()

    return add_task_to_contest_view(request, contest)


@staff_required
def edit(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)

    if request.method == 'POST':
        form = forms.TaskBasedContestForm(data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)

                contest_data = copy.copy(form.cleaned_data)
                del contest_data['by_categories_tasks_opening_policy']
                del contest_data['manual_tasks_opening_policy']

                new_contest = models.TaskBasedContest(
                    **contest_data
                )
                new_contest.id = contest.id
                new_contest.save()

                if new_contest.tasks_grouping == models.TasksGroping.ByCategories:
                    if not hasattr(contest, 'categories_list'):
                        categories_models.ContestCategories(contest=new_contest).save()
                elif contest.tasks_grouping == models.TasksGroping.OneByOne:
                    if not hasattr(contest, 'tasks_list'):
                        tasks_models.ContestTasks(contest=new_contest).save()

                # Remove all old tasks opening policies
                # It's not just call contest.tasks_opening_policies.all().delete() because of
                # django + django-polymorphic + postgresql bug:
                # https://github.com/django-polymorphic/django-polymorphic/issues/34
                for policy in contest.tasks_opening_policies.all():
                    policy.delete()

                # And create new
                if form.cleaned_data['by_categories_tasks_opening_policy'] != '-':
                    tasks_models.ByCategoriesTasksOpeningPolicy(
                        contest=contest,
                        opens_for_all_participants=form.cleaned_data['by_categories_tasks_opening_policy'] == 'E'
                    ).save()

                if form.cleaned_data['manual_tasks_opening_policy']:
                    tasks_models.ManualTasksOpeningPolicy(
                        contest=contest
                    ).save()

            messages.success(request, 'Contest «%s» has been updated' % new_contest.name)
            return redirect(contest)
    else:
        contest_data = copy.copy(contest.__dict__)

        by_categories = contest.tasks_opening_policies.instance_of(tasks_models.ByCategoriesTasksOpeningPolicy).first()
        contest_data['by_categories_tasks_opening_policy'] =\
            '-' if by_categories is None else ['T', 'E'][by_categories.opens_for_all_participants]

        manual = contest.tasks_opening_policies.instance_of(tasks_models.ManualTasksOpeningPolicy).first()
        contest_data['manual_tasks_opening_policy'] = manual is not None

        form = forms.TaskBasedContestForm(initial=contest_data)

    return render(request, 'contests/edit.html', {
        'current_contest': contest,

        'form': form
    })


def task_file(request, contest_id, file_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if not contest.is_visible_in_list and not request.user.is_staff:
        return HttpResponseNotFound()

    file = get_object_or_404(tasks_models.TaskFile, pk=file_id)
    if not contest.has_task(file.task):
        return HttpResponseNotFound()

    if not contest.is_started() and not request.user.is_staff:
        return HttpResponseForbidden('Contest is not started')

    participant = contest.get_participant_for_user(request.user)
    if not is_task_open(contest, file.task, participant) and not request.user.is_staff:
        return HttpResponseForbidden('Task is closed')

    if file.participant is not None and file.participant.id != request.user.id:
        return HttpResponseForbidden()

    file_path = file.get_path_abspath()
    return respond_as_attachment(request, file_path, file.name, file.content_type)


@staff_required
@require_POST
def delete_task(request, contest_id, task_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    task = get_object_or_404(tasks_models.Task, pk=task_id)
    if not contest.has_task(task):
        return HttpResponseNotFound()

    task.delete()

    return redirect(urlresolvers.reverse('contests:tasks', args=[contest.id]))


def news(request, contest_id, news_id):
    contest = get_object_or_404(models.Contest, pk=contest_id)
    news = get_object_or_404(models.News, pk=news_id)

    if news.contest_id != contest.id:
        return HttpResponseNotFound()

    # Only staff can see unpublished news
    if not news.is_published and not request.user.is_staff:
        return HttpResponseNotFound()

    return render(request, 'contests/news.html', {
        'current_contest': contest,

        'contest': contest,
        'news': news
    })


@staff_required
def add_news(request, contest_id):
    contest = get_object_or_404(models.Contest, pk=contest_id)

    if request.method == 'POST':
        form = forms.NewsForm(data=request.POST)
        if form.is_valid():
            news = models.News(author=request.user, contest=contest, **form.cleaned_data)
            news.save()

            messages.success(request, 'News added')

            return redirect(news)
    else:
        form = forms.NewsForm(initial={'publish_time': datetime.datetime.now()})

    return render(request, 'contests/add_news.html', {
        'current_contest': contest,

        'contest': contest,
        'form': form,
    })


@staff_required
def edit_news(request, contest_id, news_id):
    contest = get_object_or_404(models.Contest, pk=contest_id)
    news = get_object_or_404(models.News, pk=news_id)

    if contest.id != news.contest_id:
        return HttpResponseNotFound()

    if request.method == 'POST':
        form = forms.NewsForm(data=request.POST)
        if form.is_valid():
            new_news = models.News(
                author=news.author,
                contest=contest,
                created_at=news.created_at,
                updated_at=news.updated_at,
                **form.cleaned_data
            )
            new_news.id = news.id
            new_news.save()

            messages.success(request, 'News saved')

            return redirect(new_news)
    else:
        form = forms.NewsForm(initial=news.__dict__)

    return render(request, 'contests/edit_news.html', {
        'current_contest': contest,

        'contest': contest,
        'news': news,
        'form': form,
    })


@staff_required
def task_opens(request, contest_id, task_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    task = get_object_or_404(tasks_models.Task, pk=task_id)
    if not contest.has_task(task):
        return HttpResponseNotFound()

    participants = sorted(contest.participants.all(), key=operator.attrgetter('name'))
    for participant in participants:
        participant.is_task_open = is_task_open(contest, task, participant)

    is_manual_task_opening_available = is_manual_task_opening_available_in_contest(contest)

    return render(request, 'contests/task_opens.html', {
        'current_contest': contest,

        'contest': contest,
        'task': task,
        'participants': participants,
        'is_manual_task_opening_available': is_manual_task_opening_available,
    })


@staff_required
@require_POST
def open_task(request, contest_id, task_id, participant_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    task = get_object_or_404(tasks_models.Task, pk=task_id)
    if not contest.has_task(task):
        return HttpResponseNotFound()

    if not is_manual_task_opening_available_in_contest(contest):
        messages.error(request, 'Manual task opening is forbidden for this contest')
        return redirect(urlresolvers.reverse('contests:task_opens', args=[contest.id, task.id]))

    participant = get_object_or_404(models.AbstractParticipant, pk=participant_id)
    if participant.contest_id != contest.id:
        return HttpResponseNotFound()

    qs = tasks_models.ManualOpenedTask.objects.filter(
        contest=contest,
        task=task,
        participant=participant
    )
    # Toggle opens state: close if it's open, open otherwise
    if qs.exists():
        qs.delete()
        if is_task_open(contest, task, participant):
            messages.warning(request, 'Task is opened for this participant not manually, you can\'t close it')
        else:
            messages.success(request, 'Task is closed for %s' % participant.name)
    else:
        tasks_models.ManualOpenedTask(
            contest=contest,
            task=task,
            participant=participant
        ).save()
        messages.success(request, 'Task is opened for %s' % participant.name)

    return JsonResponse({'done': 'ok'})
