import djchoices
import polymorphic.models
from cached_property import cached_property
from django.core import urlresolvers
from django.db import models
from django.utils import timezone

import drapo.models
import teams.models
import users.models
from drapo.models import ModelWithTimestamps


class ContestRegistrationType(djchoices.DjangoChoices):
    Open = djchoices.ChoiceItem()
    Moderated = djchoices.ChoiceItem()
    Closed = djchoices.ChoiceItem()


class ContestParticipationMode(djchoices.DjangoChoices):
    Individual = djchoices.ChoiceItem()
    Team = djchoices.ChoiceItem()


class TasksGroping(djchoices.DjangoChoices):
    ByCategories = djchoices.ChoiceItem(label='By categories')
    OneByOne = djchoices.ChoiceItem(label='One by one')


class Contest(polymorphic.models.PolymorphicModel):
    name = models.TextField(help_text='Contest name')

    is_visible_in_list = models.BooleanField(default=False)

    registration_type = models.CharField(
        max_length=20,
        choices=ContestRegistrationType.choices,
        validators=[ContestRegistrationType.validator]
    )

    participation_mode = models.CharField(
        max_length=20,
        choices=ContestParticipationMode.choices,
        validators=[ContestParticipationMode.validator]
    )

    start_time = models.DateTimeField(help_text='Contest start time')

    finish_time = models.DateTimeField(help_text='Contest finish time')

    registration_start_time = models.DateTimeField(
        help_text='Contest registration start time, only for open and moderated registrations',
        blank=True,
        null=True
    )

    registration_finish_time = models.DateTimeField(
        help_text='Contest registration finish time, only for open and moderated registration',
        blank=True,
        null=True
    )

    short_description = models.TextField(
        help_text='Shows on main page'
    )

    description = models.TextField(
        help_text='Full description. Supports MarkDown'
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return urlresolvers.reverse('contests:contest', args=[self.id])

    def is_user_participating(self, user):
        if self.participation_mode == ContestParticipationMode.Individual:
            return self.participants.filter(individualparticipant__user=user).exists()
        elif self.participation_mode == ContestParticipationMode.Team:
            return self.participants.filter(teamparticipant__team__members=user).exists()
        else:
            raise ValueError('Unknown participation mode: %s' % (self.participation_mode,))

    def get_user_team(self, user):
        """
        Return Team object for user if contest is team-based and user is a participant
        Otherwise return None
        """
        if self.participation_mode != ContestParticipationMode.Team:
            return None

        team_participant = self.get_participant_for_user(user)
        if team_participant is None:
            return None

        return team_participant.team

    def get_participant_for_user(self, user):
        """ Returns IndividualParticipant or TeamParticipant """
        participant = None

        if user.is_anonymous():
            return None

        if self.participation_mode == ContestParticipationMode.Team:
            participant = self.participants.filter(teamparticipant__team__members=user).first()
        if self.participation_mode == ContestParticipationMode.Individual:
            participant = self.participants.filter(individualparticipant__user=user).first()

        return participant

    def can_register_now(self):
        return (self.registration_type in [ContestRegistrationType.Open, ContestRegistrationType.Moderated] and
                self.registration_start_time <= timezone.now() < self.registration_finish_time)

    def can_register_in_future(self):
        return (self.registration_type in [ContestRegistrationType.Open, ContestRegistrationType.Moderated] and
                timezone.now() < self.registration_start_time)

    def is_running(self):
        return self.start_time <= timezone.now() < self.finish_time

    def is_finished(self):
        return self.finish_time <= timezone.now()

    def is_started(self):
        return self.start_time <= timezone.now()

    def show_menu_on_top(self):
        return self.is_started()

    def is_team(self):
        return self.participation_mode == ContestParticipationMode.Team

    def is_individual(self):
        return self.participation_mode == ContestParticipationMode.Individual


class TaskBasedContest(Contest):
    tasks_grouping = models.CharField(
        max_length=20,
        choices=TasksGroping.choices,
        validators=[TasksGroping.validator]
    )

    @cached_property
    def categories(self):
        if self.tasks_grouping != TasksGroping.ByCategories:
            return []

        return list(self.categories_list.categories.all())

    @cached_property
    def tasks(self):
        if self.tasks_grouping != TasksGroping.OneByOne:
            return []

        return list(self.tasks_list.tasks.all())

    def get_tasks_solved_by_participant(self, participant):
        """ Returns task ids for solved by participant tasks """
        return set(self.attempts
                       .filter(participant=participant, is_checked=True, is_correct=True)
                       .values_list('task_id', flat=True)
                   )

    def has_task(self, task):
        if self.tasks_grouping == TasksGroping.OneByOne:
            return task in self.tasks
        if self.tasks_grouping == TasksGroping.ByCategories:
            return self.categories_list.categories.filter(tasks=task).exists()


class AbstractParticipant(polymorphic.models.PolymorphicModel, drapo.models.ModelWithTimestamps):
    contest = models.ForeignKey(Contest, related_name='participants')

    is_approved = models.BooleanField(default=True)

    is_disqualified = models.BooleanField(default=False)

    is_visible_in_scoreboard = models.BooleanField(default=True)

    @property
    def name(self):
        return self.get_real_instance().name

    def get_absolute_url(self):
        return self.get_real_instance().get_absolute_url()


class IndividualParticipant(AbstractParticipant):
    user = models.ForeignKey(users.models.User, related_name='individual_participant_in')

    def __str__(self):
        return str(self.user)

    @property
    def name(self):
        return self.user.get_full_name()

    def get_absolute_url(self):
        return self.user.get_absolute_url()


class TeamParticipant(AbstractParticipant):
    team = models.ForeignKey(teams.models.Team, related_name='participant_in')

    def __str__(self):
        return str(self.team)

    @property
    def name(self):
        return self.team.name

    def get_absolute_url(self):
        return self.team.get_absolute_url()


class AbstractAdditionalScorer(polymorphic.models.PolymorphicModel):
    """ Defines additional scores policy """
    contest = models.ForeignKey(Contest, related_name='additional_scorers')


class ScoreByPlaceAdditionalScorer(AbstractAdditionalScorer):
    """ Additional scores to first solved task teams """
    place = models.PositiveIntegerField(help_text='I.e. 1 for team who first solved the task')

    points = models.IntegerField()

    def __str__(self):
        return '%d additional points for %d team' % (self.points, self.place)


class News(ModelWithTimestamps):
    contest = models.ForeignKey(Contest, related_name='news')

    author = models.ForeignKey(users.models.User, related_name='+')

    title = models.CharField(max_length=1000, help_text='Title')

    text = models.TextField(help_text='Supports markdown')

    is_published = models.BooleanField(default=False)

    publish_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'News'

    def get_absolute_url(self):
        return urlresolvers.reverse('contests:news', args=[self.contest_id, self.id])
