from django import forms

from bootstrap3_datetime.widgets import DateTimePicker

from . import models
import taskbased.tasks.models as tasks_models


class ChooseTeamForm(forms.Form):
    team = forms.TypedChoiceField(
        label='Select team',
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
        label='Invite hash',
        max_length=32,
        widget=forms.TextInput()
    )


class CreateCategoryForm(forms.Form):
    name = forms.CharField(
        label='Category name',
        max_length=100,
        widget=forms.TextInput(attrs={
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    description = forms.CharField(
        label='Description',
        help_text='Supports markdown',
        max_length=500,
        widget=forms.Textarea()
    )


class TaskBasedContestForm(forms.Form):
    name = forms.CharField(
        label='Name',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'autofocus': 'autofocus',
            'class': 'form-control-short',
        })
    )

    short_description = forms.CharField(
        label='Short description',
        help_text='Shows on main page',
        required=True,
        widget=forms.TextInput()
    )

    description = forms.CharField(
        label='Description',
        help_text='Full description. Supports MarkDown',
        required=True,
        widget=forms.Textarea()
    )

    is_visible_in_list = forms.BooleanField(
        label='Visible in list?',
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
        label='Participation mode',
        max_length=20,
        widget=forms.Select(
            choices=models.ContestParticipationMode.choices,
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    start_time = forms.DateTimeField(
        label='Start',
        required=True,
        help_text='Contest start time',
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    finish_time = forms.DateTimeField(
        label='Finish',
        required=True,
        help_text='Contest finish time',
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    registration_start_time = forms.DateTimeField(
        label='Registration start',
        help_text='Contest registration start time, only for open and moderated registrations',
        required=False,
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    registration_finish_time = forms.DateTimeField(
        label='Registration finish',
        help_text='Contest registration finish time, only for open and moderated registrations',
        required=False,
        widget=DateTimePicker(
            options={'format': 'YYYY-MM-DD HH:mm'},
            attrs={
                'class': 'form-control-short'
            }
        )
    )

    tasks_grouping = forms.CharField(
        label='Task grouping',
        help_text='Enable categories or list all tasks one by one',
        max_length=20,
        widget=forms.Select(
            choices=models.TasksGroping.choices,
            attrs={
                'class': 'form-control-short'
            }
        )
    )


class ManualRegisterParticipant(forms.Form):
    participant_link = forms.CharField(
        label='Link',
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Link to user or team for registering to the contest. I.e. http://drapo.io/users/1',
            'class': 'input-sm mr15',
            'style': 'width: 500px; height: 30px;'
        })
    )


class CreateTaskForm(forms.Form):
    name = forms.CharField(
        label='Name',
        help_text='Shows on tasks page',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control-short'
        }),
    )

    max_score = forms.IntegerField(
        label='Max score',
        min_value=0,
        max_value=10000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control-short'
        }),
    )

    statement_title = forms.CharField(
        label='Title',
        help_text='Statement title. Supports markdown and substitutes',
    )

    statement_template = forms.CharField(
        label='Template',
        help_text='Statement template. Supports markdown and substitutes',
        widget=forms.Textarea(),
    )

    statement_files = forms.FileField(
        label='Files',
        help_text='Files will be attached to the statement. Up to 10 files',
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
        label='Answer',
        widget=forms.TextInput(attrs={
            'class': 'form-control-short'
        }),
    )

    case_sensitive = forms.BooleanField(
        label='Is case sensitive',
        required=False,
    )

    def get_checker(self):
        return tasks_models.TextChecker(
            answer=self.cleaned_data['answer'],
            case_sensitive=self.cleaned_data['case_sensitive'],
        )


class CreateRegExpCheckerForm(AbstractCheckerForm):
    pattern = forms.CharField(
        label='Pattern',
        help_text='Regular expression for matching, don\'t need ^ and $',
        widget=forms.TextInput(attrs={
            'class': 'form-control-short'
        }),
    )

    flag_ignore_case = forms.BooleanField(
        label='Ignore case',
        help_text='Python\'s re.IGNORECASE (re.I)',
        required=False,
    )

    flag_multiline = forms.BooleanField(
        label='Multiline',
        help_text='Python\'s re.MULTILINE (re.M)',
        required=False,
    )

    flag_dotall = forms.BooleanField(
        label='Dot (.) includes newline character',
        help_text='Python\'s re.DOTALL (re.S)',
        required=False,
    )

    flag_verbose = forms.BooleanField(
        label='Verbose',
        help_text='Python\'s re.VERBOSE (re.X)',
        required=False,
    )

    def get_checker(self):
        return tasks_models.RegExpChecker(
            answer=self.cleaned_data['answer'],
            flag_ignore_case=self.cleaned_data['flag_ignore_case'],
            flag_multiline=self.cleaned_data['flag_multiline'],
            flag_dotall=self.cleaned_data['flag_dotall'],
            flag_verbose=self.cleaned_data['flag_verbose'],
        )
