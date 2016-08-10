from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _


class AttemptForm(forms.Form):
    answer = forms.CharField(
        label=_('Answer'),
        required=True,
        max_length=1000,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your answer',
            'autofocus': 'autofocus',
        })
    )


class EditAttemptForm(forms.Form):
    answer = forms.CharField(
        label=_('Answer'),
        max_length=1000,
        widget=forms.TextInput(attrs={
            'autofocus': 'autofocus',
            'class': 'form-control-short'
        })
    )

    is_checked = forms.BooleanField(
        label=_('Checked?'),
        required=False,
    )

    score = forms.IntegerField(
        label=_('Score'),
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-short'
        })
    )

    public_comment = forms.CharField(
        label=_('Public comment'),
        help_text=_('Visible to participant'),
        required=False,
        widget=forms.Textarea()
    )

    private_comment = forms.CharField(
        label=_('Private comment'),
        help_text=_('Visible only to admins'),
        required=False,
        widget=forms.Textarea()
    )

    def __init__(self, attempt, *args, **kwargs):
        if 'initial' in kwargs:
            del kwargs['initial']
        super().__init__(initial=attempt.__dict__, *args, **kwargs)
        self.fields['score'].validators.append(validators.MaxValueValidator(attempt.task.max_score))
        self.fields['score'].help_text = 'Out of %d' % attempt.task.max_score
