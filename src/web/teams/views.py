from django.contrib import messages
from django.core import urlresolvers
from django.db import transaction
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.conf import settings

from users.decorators import login_required
from . import models
from . import forms
import contests.models as contests_models
import users.models as users_models


def teams_list(request):
    teams = models.Team.objects.all()
    return render(request, 'teams/list.html', {
        'teams': teams
    })


def team(request, team_id):
    team = get_object_or_404(models.Team, pk=team_id)
    members = list(team.members.all())
    contests = contests_models.Contest.objects.filter(participants__teamparticipant__team=team)
    can_edit = request.user.is_staff or \
        (not settings.DRAPO_ONLY_STAFF_CAN_EDIT_TEAM_NAME and team.captain_id == request.user.id)

    return render(request, 'teams/team.html', {
        'team': team,
        'members': members,
        'contests': contests,
        'can_edit': can_edit,
    })


class TeamCreationException(Exception):
    pass


def create_team(team_name, captain):
    team = models.Team(
        name=team_name,
        captain=captain,
    )
    with transaction.atomic():
        if settings.DRAPO_USER_CAN_BE_ONLY_IN_ONE_TEAM and \
                models.Team.objects.filter(members=captain).exists() and \
                not captain.is_staff:
            user_team = models.Team.objects.filter(members=captain).first()
            raise TeamCreationException(
                'You can\'t create a new team while you are a member of team %s' % user_team.name
            )
        if settings.DRAPO_TEAM_NAMES_ARE_UNIQUE and \
                models.Team.objects.filter(name=team_name).exists() and \
                not captain.is_staff:
            raise TeamCreationException('Team with same name already exists')
        team.save()
        team.members.add(captain)
        team.save()
    return team


@login_required
def create(request):
    if request.method == 'POST':
        form = forms.TeamForm(data=request.POST)
        if form.is_valid():
            team_name = form.cleaned_data['name']
            try:
                team = create_team(team_name, request.user)
            except TeamCreationException as e:
                form.add_error('name', str(e))
                messages.error(request, str(e))
            else:
                messages.success(request, 'Team ' + team.name + ' created')

                if 'next' in request.GET and '//' not in request.GET['next']:
                    return redirect(request.GET['next'])

                return redirect(team.get_absolute_url())

    else:
        form = forms.TeamForm()

    return render(request, 'teams/create.html', {
        'form': form
    })


@login_required
def join(request, invite_hash=None):
    if request.method == 'POST' and 'invite_hash' in request.POST:
        invite_hash = request.POST['invite_hash']

    team = models.Team.objects.filter(invite_hash=invite_hash).first()
    error_message = None

    if team is None:
        error_message = 'Team not found. Return back and try one more time'

    if request.method == 'POST' and team is not None:
        if team.members.count() > settings.DRAPO_TEAM_SIZE_LIMIT:
            messages.error('You can\'t join the team because it\'s very big (%d members)' % team.members.count())
        else:
            with transaction.atomic():
                if request.user in team.members.all():
                    messages.warning(request, 'You are already in team ' + team.name)
                    if 'next' in request.POST and '//' not in request.POST['next']:
                        return redirect(request.POST['next'])
                    return redirect(urlresolvers.reverse('teams:team', args=[team.id]))

                if settings.DRAPO_USER_CAN_BE_ONLY_IN_ONE_TEAM and \
                        models.Team.objects.filter(members=request.user).exists() and \
                        not request.user.is_staff:
                    messages.error(request,
                                   'You can\'t join team %s while you are a member of another team' % team.name)
                    if 'next' in request.POST and '//' not in request.POST['next']:
                        return redirect(request.POST['next'])
                    return redirect(urlresolvers.reverse('teams:team', args=[team.id]))

                team.members.add(request.user)
                team.save()

            messages.success(request, 'You joined team ' + team.name + '!')

        if 'next' in request.POST and '//' not in request.POST['next']:
            return redirect(request.POST['next'])
        return redirect(urlresolvers.reverse('teams:team', args=[team.id]))
    elif request.method == 'GET':
        if team is None:
            return HttpResponseNotFound()

    return render(request, 'teams/join.html', {
        'error_message': error_message,
        'team': team
    })


@login_required
@require_POST
def leave(request, team_id):
    team = get_object_or_404(models.Team, pk=team_id)

    if team.captain == request.user:
        messages.error(request, 'Captain can\'t leave the team.')
    else:
        with transaction.atomic():
            if request.user not in team.members.all():
                return HttpResponseNotFound()

            team.members.remove(request.user)

        messages.success(request, 'You have been left the team %s' % team.name)

        if 'next' in request.POST and '//' not in request.POST['next']:
            return redirect(request.POST['next'])
    return redirect(urlresolvers.reverse('teams:team', args=[team.id]))


@login_required
def edit(request, team_id):
    team = get_object_or_404(models.Team, pk=team_id)

    # Only staff and team's captain can edit team
    if not request.user.is_staff and team.captain != request.user:
        return HttpResponseNotFound()

    if settings.DRAPO_ONLY_STAFF_CAN_EDIT_TEAM_NAME and not request.user.is_staff:
        return HttpResponseNotFound()

    if request.method == 'POST':
        form = forms.TeamForm(data=request.POST)
        if form.is_valid():
            team_name = form.cleaned_data['name']
            with transaction.atomic():
                if models.Team.objects.filter(name=team_name).exists():
                    form.add_error('name', 'Team with same name already exists')
                else:
                    team.name = team_name
                    team.save()

                    messages.success(request, 'Team %s saved' % team.name)
                    return redirect(team)
    else:
        form = forms.TeamForm(initial={'name': team.name})

    return render(request, 'teams/edit.html', {
        'team': team,
        'form': form,
    })


@login_required
@require_POST
def remove_member(request, team_id, user_id):
    team = get_object_or_404(models.Team, pk=team_id)

    # Only staff and team's captain can edit team
    if not request.user.is_staff and team.captain != request.user:
        return HttpResponseNotFound()

    user = get_object_or_404(users_models.User, pk=user_id)

    with transaction.atomic():
        if user == team.captain:
            messages.warning(request, 'Captain can\'t leave the team')
            return redirect(team)

        if user not in team.members.all():
            messages.warning(request, 'User %s not in the team' % (user.username,))
            return redirect(team)

        team.members.remove(user)
        team.save()

    messages.success(request, 'User %s has left the team %s' % (user.username, team.name))

    return redirect(team)
