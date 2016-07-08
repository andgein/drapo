from django import forms


class CreateTeamForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label='Team name',
        widget=forms.TextInput(attrs={
            'class': 'form-control-short',
        })
    )
