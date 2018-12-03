from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core import urlresolvers
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from . import forms
from . import models
from contests.models import Contest, IndividualParticipant


def profile(request, user_id):
    user = get_object_or_404(models.User, pk=user_id)
    user_teams = list(user.teams.all())
    is_current_user = user.id == request.user.id

    if not (is_current_user or request.user.is_staff):
        return redirect_to_login(request.build_absolute_uri())

    return render(request, 'users/profile.html', {
        'profile_user': user,
        'user_teams': user_teams,
        'is_current_user': is_current_user
    })


def login(request):
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            email_or_login = form.cleaned_data['email_or_login'].lower()
            user = models.User.objects.filter(Q(email__iexact=email_or_login) | Q(username__iexact=email_or_login)).first()
            if user is not None and user.check_password(form.cleaned_data['password']):
                if user.is_email_confirmed:
                    auth.login(request, user)

                    if 'next' in request.GET and '//' not in request.GET['next']:
                        return redirect(request.GET['next'])
                    return redirect('home')

                form.add_error('email_or_login', 'Confirm your email by clicking link in email from your inbox')
            else:
                form.add_error('email_or_login', 'Wrong email/login or password')
    else:
        form = forms.LoginForm()

    return render(request, 'users/login.html', {
        'form': form
    })


def register(request):
    if request.method == 'POST':
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']
            team_name = form.cleaned_data['team_name']

            with transaction.atomic():
                if models.User.objects.filter(username=username).exists():
                    form.add_error('username', 'This username is already taken')
                elif models.User.objects.filter(email=email).exists():
                    form.add_error('email', 'User with this email already exists')
                else:
                    user = models.User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=team_name,
                        password=password
                    )

                    confirmation = models.EmailConfirmation(user=user, is_confirmed=True)
                    confirmation.save()

                    IndividualParticipant(
                        contest=Contest.objects.get(id=settings.QCTF_CONTEST_ID),
                        user=user
                    ).save()

                    return redirect_to_login(request.build_absolute_uri())

    else:
        form = forms.RegisterForm()

    return render(request, 'users/register.html', {
        'form': form
    })


@require_POST
def logout(request):
    if request.user.is_authenticated():
        auth.logout(request)

    if 'next' in request.POST and '//' not in request.POST['next']:
        return redirect(request.POST['next'])
    return redirect('home')


def confirm(request, token):
    confirmation = get_object_or_404(models.EmailConfirmation, token=token, is_confirmed=False)
    confirmation.is_confirmed = True
    confirmation.save()

    user = confirmation.user
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth.login(request, user)

    messages.success(request, 'Your account has been confirmed')

    return redirect(urlresolvers.reverse('home'))


@login_required
def edit(request):
    user = request.user

    if request.method == 'POST':
        form = forms.EditUserForm(user, data=request.POST)
        if form.is_valid():
            new_username = form.cleaned_data['username']
            changed_username = new_username != user.username
            with transaction.atomic():
                if changed_username and models.User.objects.filter(username=new_username).exists():
                    form.add_error('username', 'This username is already taken')
                else:
                    user.username = new_username
                    user.first_name = form.cleaned_data['first_name']
                    user.last_name = form.cleaned_data['last_name']
                    user.save()
                    messages.success(request, 'Your settings has been changed')
                    return redirect(urlresolvers.reverse('users:edit'))
    else:
        form = forms.EditUserForm(user)

    password_form = forms.ChangePasswordForm()

    return render(request, 'users/edit.html', {
        'form': form,
        'password_form': password_form
    })


@login_required
@require_POST
def change_password(request):
    form = forms.ChangePasswordForm(data=request.POST)
    if form.is_valid():
        if not request.user.check_password(form.cleaned_data['old_password']):
            form.add_error('old_password', 'Password isn\'t correct')
        else:
            request.user.set_password(form.cleaned_data['password'])
            request.user.save()

            messages.success(request, 'Your password has been changed')
            return redirect(urlresolvers.reverse('users:edit'))

    user_form = forms.EditUserForm(request.user)

    return render(request, 'users/edit.html', {
        'form': user_form,
        'password_form': form
    })
