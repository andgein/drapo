import itertools
import operator
import re

import collections
from django.contrib import messages
from django.core import urlresolvers
from django.db import transaction
from django.http.response import Http404, HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from users.decorators import login_required, staff_required
import users.models as users_models
from . import models
from . import forms
import teams.models as teams_models
import taskbased.categories.models as categories_models
import taskbased.tasks.models as tasks_models
import taskbased.tasks.forms as tasks_forms


def _groupby(iterable, keyfunc):
    return {k: list(v) for k, v in itertools.groupby(iterable, keyfunc)}


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
            return Http404()

    is_current_user_participating = request.user.is_authenticated() and contest.is_user_participating(request.user)
    is_team_contest = contest.participation_mode == models.ContestParticipationMode.Team

    # Contest.get_user_team() returns None if contest isn't team-based or user is not participating
    current_user_team = contest.get_user_team(request.user)
    current_user_participant = contest.get_participant_for_user(request.user)

    participants = contest.participants.filter(is_approved=True)

    return render(request, 'contests/contest.html', {
        'current_contest': contest,

        'contest': contest,
        'is_current_user_participating': is_current_user_participating,
        'current_user_participant': current_user_participant,
        'is_team_contest': is_team_contest,
        'current_user_team': current_user_team,
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

    if contest.tasks_grouping == models.TasksGroping.OneByOne:
        tasks = contest.tasks
        return render(request, 'contests/tasks_one_by_one.html', {
            'current_contest': contest,

            'contest': contest,
            'tasks': tasks,
            'solved_tasks_ids': solved_tasks_ids
        })
    if contest.tasks_grouping == models.TasksGroping.ByCategories:
        categories = contest.categories
        return render(request, 'contests/tasks_by_categories.html', {
            'current_contest': contest,

            'contest': contest,
            'categories': categories,
            'solved_tasks_ids': solved_tasks_ids
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
                                  key=lambda p: (-scores_by_participant[p.id], last_success_time_by_participant[p.id])
                                  )

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


def task(request, contest_id, task_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if not contest.is_visible_in_list and not request.user.is_staff:
        return HttpResponseNotFound()

    task = get_object_or_404(tasks_models.Task, pk=task_id)
    if not contest.has_task(task):
        return HttpResponseNotFound()

    if request.method == 'POST' and request.user.is_authenticated():
        form = tasks_forms.AttemptForm(data=request.POST)
        if form.is_valid():
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
        'participant': contest.get_participant_for_user(request.user)
    })

    return render(request, 'contests/task.html', {
        'current_contest': contest,

        'contest': contest,
        'task': task,
        'statement': statement,
        'attempt_form': form
    })


@staff_required
def add_category(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)
    if request.method == 'POST':
        form = forms.CreateCategoryForm(data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                category = categories_models.Category(
                    name=form.cleaned_data['name'],
                    description=form.cleaned_data['description']
                )
                category.save()

                contest.categories_list.categories.add(category)
                contest.save()
            return redirect(urlresolvers.reverse('contests:tasks', args=[contest.id]))
    else:
        form = forms.CreateCategoryForm()

    return render(request, 'contests/create_category.html', {
        'current_contest': contest,

        'contest': contest,
        'form': form,
    })


@staff_required
def attempts(request, contest_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)

    attempts = contest.attempts.order_by('-created_at').select_related('task', 'participant', 'author')

    return render(request, 'contests/attempts.html', {
        'current_contest': contest,

        'contest': contest,
        'attempts': attempts,
    })


@staff_required
def create(request):
    if request.method == 'POST':
        form = forms.CreateTaskBasedContestForm(data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                contest = models.TaskBasedContest(
                    **form.cleaned_data
                )
                contest.save()
                if contest.tasks_grouping == models.TasksGroping.ByCategories:
                    categories_models.ContestCategories(contest=contest).save()
                elif contest.tasks_grouping == models.TasksGroping.OneByOne:
                    tasks_models.ContestTasks(contest=contest).save()
            messages.success(request, 'Contest «%s» created' % contest.name)
            return redirect(contest)
    else:
        form = forms.CreateTaskBasedContestForm()

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

                print(link)

                if match is None:
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


@staff_required
def add_task_to_category(request, contest_id, category_id):
    contest = get_object_or_404(models.TaskBasedContest, pk=contest_id)

    category = get_object_or_404(categories_models.Category, pk=category_id, contestcategories__contest_id=contest_id)

    if request.method == 'POST':
        form = forms.CreateTaskForm(data=request.POST)
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

                    category.tasks.add(task)
                    category.save()

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
