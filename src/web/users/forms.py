from django import forms
from django.contrib.auth.forms import PasswordResetForm, \
    default_token_generator, get_current_site, force_bytes, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _


class LoginForm(forms.Form):
    email_or_login = forms.CharField(
        required=True,
        label='Логин',
        max_length=100,
        widget=forms.TextInput(attrs={
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    password = forms.CharField(
        required=True,
        label='Пароль',
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control-short',
        })
    )


class FormWithRepeatedPassword(forms.Form):
    password = forms.CharField(
        required=True,
        label='Пароль',
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control-short',
        })
    )

    password_repeat = forms.CharField(
        required=True,
        label='Повторите пароль',
        max_length=128,
        widget=forms.PasswordInput(attrs={
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
        label='Имя пользователя',
        max_length=100,
        widget=forms.TextInput(attrs={
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    email = forms.EmailField(
        required=True,
        label='E-mail',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control-short',
        })
    )

    team_name = forms.CharField(
        label='Название команды (в таблице результатов)',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control-short',
        })
    )

    def __init__(self, *args, **kwargs):
        if 'field_order' in kwargs:
            del kwargs['field_order']
        super().__init__(field_order=['username', 'email', 'team_name', 'password', 'password_validation'],
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


class VerbosePasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not list(self.get_users(email)):
            raise forms.ValidationError('Команды, где капитан имеет такой e-mail, не существует')

        return email
