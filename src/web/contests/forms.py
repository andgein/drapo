from django import forms
from django.utils.translation import ugettext_lazy as _

from bootstrap3_datetime.widgets import DateTimePicker

from . import models
import taskbased.tasks.models as tasks_models


class ChooseTeamForm(forms.Form):
    team = forms.TypedChoiceField(
        label=_('Select team'),
        coerce=int,
        widget=forms.Select(attrs={
            'class': 'form-control-short'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_teams = [(team.id, team.name) for team in user.teams.all()]
        self.fields['team'].choices = user_teams


class JoinViaInviteHashForm(forms.Form):
    invite_hash = forms.CharField(
        label=_('Invite hash'),
        max_length=32,
        widget=forms.TextInput(attrs={
            'placeholder': 'Invite hash',
            'class': 'form-control-short form-control-small'
        })
    )


class CategoryForm(forms.Form):
    name = forms.CharField(
        label=_('Category name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    description = forms.CharField(
        label=_('Description'),
        help_text='Supports markdown',
        max_length=500,
        widget=forms.Textarea()
    )


class TaskBasedContestForm(forms.Form):
    name = forms.CharField(
        label=_('Name'),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    short_description = forms.CharField(
        label=_('Short description'),
        help_text=_('Shows on main page'),
        required=True,
        widget=forms.TextInput()
    )

    description = forms.CharField(
        label=_('Description'),
        help_text=_('Full description. Supports MarkDown'),
        required=True,
        widget=forms.Textarea()
    )

    is_visible_in_list = forms.BooleanField(
        label=_('Visible in list?'),
        required=False,
        widget=forms.CheckboxInput()
    )

    registration_type = forms.CharField(
        label='Registration type',
        max_length=20,
        widget=forms.Select(
            choices=models.ContestRegistrationType.choices,
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    participation_mode = forms.CharField(
        label=_('Participation mode'),
        max_length=20,
        widget=forms.Select(
            choices=models.ContestParticipationMode.choices,
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    start_time = forms.DateTimeField(
        label=_('Start'),
        required=True,
        help_text=_('Contest start time'),
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    finish_time = forms.DateTimeField(
        label=_('Finish'),
        required=True,
        help_text=_('Contest finish time'),
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    registration_start_time = forms.DateTimeField(
        label=_('Registration start'),
        help_text=_('Contest registration start time, only for open and moderated registrations'),
        required=False,
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    registration_finish_time = forms.DateTimeField(
        label=_('Registration finish'),
        help_text=_('Contest registration finish time, only for open and moderated registrations'),
        required=False,
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    tasks_grouping = forms.CharField(
        label=_('Task grouping'),
        help_text=_('Enable categories or list all tasks one by one'),
        max_length=20,
        widget=forms.Select(
            choices=models.TasksGroping.choices,
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    by_categories_tasks_opening_policy = forms.CharField(
        label=_('Tasks opening policy: next task opening'),
        max_length=1,
        widget=forms.Select(
            choices=[('-', _('No')), ('T', _('Only for team who solved the task')), ('E', _('Task will be open for everyone'))],
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    manual_tasks_opening_policy = forms.BooleanField(
        label=_('Tasks opening policy: manual'),
        required=False,
        help_text=_('Can admins open tasks manually for everyone or one participant'),
        widget=forms.Select(
            choices=[(False, _('No')), (True, _('Yes'))],
            attrs={
                'class': 'form-control-short'
            }
        )
    )


class ManualRegisterParticipant(forms.Form):
    participant_link = forms.CharField(
        label=_('Link'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': _('Link to user or team for registering to the contest. I.e. http://drapo.io/users/1'),
            'class': 'input-sm mr15',
            'style': 'width: 500px; height: 30px;'
        })
    )


class CreateTaskForm(forms.Form):
    name = forms.CharField(
        label=_('Name'),
        help_text=_('Shows on tasks page'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control-short'
        }),
    )

    max_score = forms.IntegerField(
        label=_('Max score'),
        min_value=0,
        max_value=10000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-short'
        }),
    )

    statement_title = forms.CharField(
        label=_('Title'),
        help_text=_('Statement title. Supports markdown and substitutes'),
    )

    statement_template = forms.CharField(
        label=_('Template'),
        help_text=_('Statement template. Supports markdown and substitutes'),
        widget=forms.Textarea(),
    )

    statement_files = forms.FileField(
        label=_('Files'),
        help_text=_('Files will be attached to the statement. Up to 10 files'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'bootstrap-file-input',
            'multiple': 'multiple',
            'data-show-upload': 'false',
            'data-max-file-count': 10,
        })
    )

    checker_type = forms.CharField(
        widget=forms.HiddenInput(),
        initial='text',
    )


class AbstractCheckerForm(forms.Form):
    def get_checker(self):
        raise NotImplementedError()


class CreateTextCheckerForm(AbstractCheckerForm):
    answer = forms.CharField(
        label=_('Answer'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-short'
        }),
    )

    case_sensitive = forms.BooleanField(
        label=_('Is case sensitive'),
        required=False,
    )

    def get_checker(self):
        return tasks_models.TextChecker(
            answer=self.cleaned_data['answer'],
            case_sensitive=self.cleaned_data['case_sensitive'],
        )


class CreateRegExpCheckerForm(AbstractCheckerForm):
    pattern = forms.CharField(
        label=_('Pattern'),
        required=False,
        help_text=_('Regular expression for matching, don\'t need ^ and $'),
        widget=forms.TextInput(attrs={
            'class': 'form-control-short'
        }),
    )

    flag_ignore_case = forms.BooleanField(
        label=_('Ignore case'),
        help_text=_('Python\'s re.IGNORECASE (re.I)'),
        required=False,
    )

    flag_multiline = forms.BooleanField(
        label=_('Multiline'),
        help_text=_('Python\'s re.MULTILINE (re.M)'),
        required=False,
    )

    flag_dotall = forms.BooleanField(
        label=_('Dot (.) includes newline character'),
        help_text=_('Python\'s re.DOTALL (re.S)'),
        required=False,
    )

    flag_verbose = forms.BooleanField(
        label=_('Verbose'),
        help_text=_('Python\'s re.VERBOSE (re.X)'),
        required=False,
    )

    def get_checker(self):
        return tasks_models.RegExpChecker(
            pattern=self.cleaned_data['pattern'],
            flag_ignore_case=self.cleaned_data['flag_ignore_case'],
            flag_multiline=self.cleaned_data['flag_multiline'],
            flag_dotall=self.cleaned_data['flag_dotall'],
            flag_verbose=self.cleaned_data['flag_verbose'],
        )


class AttemptsSearchForm(forms.Form):
    pattern = forms.CharField(
        label=_('Search'),
        max_length=400,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'By answer, author, team name or task title',
            'class': 'form-control-short form-control-small'
        })
    )


class NewsForm(forms.Form):
    title = forms.CharField(
        label=_('Title'),
        max_length=1000,
        widget=forms.TextInput(attrs={
            'class': 'form-control-short'
        })
    )

    text = forms.CharField(
        label=_('Text'),
        help_text=_('Supports markdown'),
        widget=forms.Textarea()
    )

    is_published = forms.BooleanField(
        label=_('Is published'),
        required=False,
    )

    publish_time = forms.DateTimeField(
        label=_('Publish time'),
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )
