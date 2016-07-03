from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        label='Username',
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter username',
            'class': 'form-control'
        })
    )

    password = forms.CharField(
        required=True,
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-control'
        })
    )


class RegisterForm(forms.Form):
    username = forms.CharField(
        required=True,
        label='Username',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter username',
            'class': 'form-control'
        })
    )

    email = forms.EmailField(
        required=True,
        label='Email',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter email',
            'class': 'form-control'
        })
    )

    first_name = forms.CharField(
        label='First name',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your first name',
            'class': 'form-control'
        })
    )

    last_name = forms.CharField(
        label='Last name',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your last name',
            'class': 'form-control'
        })
    )

    password = forms.CharField(
        required=True,
        label='Password',
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-control'
        })
    )

    password_repeat = forms.CharField(
        required=True,
        label='Password again',
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-control'
        })
    )

    def clean_password_repeat(self):
        password = self.cleaned_data.get('password')
        password_repeat = self.cleaned_data.get('password_repeat')
        if password and password_repeat and password != password_repeat:
            self._errors['password_repeat'] = self.error_class(['Password are not equal'])
