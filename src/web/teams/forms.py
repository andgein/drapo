from django import forms
from django.utils.translation import ugettext_lazy as _


class TeamForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label=_('Team name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control-short',
        })
    )
