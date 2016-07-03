from django.contrib import auth
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from . import forms
from . import models


def profile(request, user_id):
    user = get_object_or_404(models.User, pk=user_id)
    user_teams = list(user.teams.all())
    is_current_user = user.id == request.user.id

    return render(request, 'users/profile.html', {
        'profile_user': user,
        'user_teams': user_teams,
        'is_current_user': is_current_user
    })


def login(request):
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                if user.is_email_confirmed:
                    auth.login(request, user)

                    if request.GET['next'] is not None and '//' not in request.GET['next']:
                        return redirect(request.GET['next'])
                    return redirect('home')

                form.add_error('username', 'Confirm your email by clicking link in email from your inbox')
            else:
                form.add_error('username', 'Wrong username of password')
    else:
        form = forms.LoginForm()

    return render(request, 'users/login.html', {
        'form': form
    })


def register(request):
    if request.method == 'POST':
        form = forms.RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                username = form.cleaned_data['username']
                email = form.cleaned_data['email']

                if models.User.objects.filter(username=username).exists():
                    form.add_error('username', 'This username is already taken')
                elif models.User.objects.filter(email=email).exists():
                    form.add_error('email', 'User with this email already exists')
                else:
                    password = form.cleaned_data['password']
                    first_name = form.cleaned_data['first_name']
                    last_name = form.cleaned_data['last_name']

                    user = models.User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        password=password
                    )
                    user.save()

                    confirmation = models.EmailConfirmation(user=user)
                    confirmation.send()
                    confirmation.save()

                    return render(request, 'message.html', {
                        'message': 'We have sent you an email with confirmation link. Please follow it.'
                    })

    else:
        form = forms.RegisterForm()

    return render(request, 'users/register.html', {
        'form': form
    })


@require_POST
def logout(request):
    if request.user.is_authenticated():
        auth.logout(request)
    return redirect('home')

