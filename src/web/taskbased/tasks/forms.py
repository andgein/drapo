from django import forms


class AttemptForm(forms.Form):
    answer = forms.CharField(
        label='Answer',
        required=True,
        max_length=1000,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your answer',
            'autofocus': 'autofocus',
        })
    )
