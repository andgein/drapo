from django import forms
from django.utils.translation import ugettext_lazy as _


class LoginForm(forms.Form):
    email = forms.CharField(
        required=True,
        label=_('Email'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Your email'),
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    password = forms.CharField(
        required=True,
        label=_('Password'),
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': _('Enter password'),
            'class': 'form-control-short',
        })
    )


class FormWithRepeatedPassword(forms.Form):
    password = forms.CharField(
        required=True,
        label=_('Password'),
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': _('Enter password'),
            'class': 'form-control-short',
        })
    )

    password_repeat = forms.CharField(
        required=True,
        label=_('Password again'),
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': _('Repeat password'),
            'class': 'form-control-short',
        })
    )

    def clean_password_repeat(self):
        password = self.cleaned_data.get('password')
        password_repeat = self.cleaned_data.get('password_repeat')
        if password and password_repeat and password != password_repeat:
            self._errors['password_repeat'] = self.error_class(['Password are not equal'])


class RegisterForm(FormWithRepeatedPassword):
    username = forms.CharField(
        required=True,
        label=_('Username'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Enter username'),
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    email = forms.EmailField(
        required=True,
        label=_('Email'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Enter email'),
            'class': 'form-control-short',
        })
    )

    first_name = forms.CharField(
        label=_('First name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Your first name'),
            'class': 'form-control-short',
        })
    )

    last_name = forms.CharField(
        label=_('Last name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Your last name'),
            'class': 'form-control-short',
        })
    )

    def __init__(self, *args, **kwargs):
        if 'field_order' in kwargs:
            del kwargs['field_order']
        super().__init__(field_order=['username', 'email', 'first_name', 'last_name', 'password', 'password_validation'],
                         *args, **kwargs)


class EditUserForm(forms.Form):
    username = forms.CharField(
        required=True,
        label=_('Username'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Your username'),
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    first_name = forms.CharField(
        label=_('First name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Your first name'),
            'class': 'form-control-short',
        })
    )

    last_name = forms.CharField(
        label=_('Last name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Your last name'),
            'class': 'form-control-short',
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }


class ChangePasswordForm(FormWithRepeatedPassword):
    old_password = forms.CharField(
        required=True,
        label=_('Old password'),
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control-short'
        })
    )

    def __init__(self, *args, **kwargs):
        if 'field_order' in kwargs:
            del kwargs['field_order']
        super().__init__(field_order=['old_password', 'password', 'password_repeat'], *args, **kwargs)
