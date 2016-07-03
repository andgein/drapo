from django.core import urlresolvers
from django.db import models

import drapo.models
import users.models
from drapo.common import generate_random_secret_string


class Team(drapo.models.ModelWithTimestamps):
    name = models.TextField(max_length=100, help_text='Team name')

    captain = models.ForeignKey(users.models.User, help_text='Team captain', related_name='captain_in')

    members = models.ManyToManyField(
        users.models.User,
        help_text='Participants (should contain captain)',
        blank=True,
        related_name='teams'
    )

    invite_hash = models.TextField(
        max_length=32,
        unique=True,
        default=generate_random_secret_string
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return urlresolvers.reverse('teams:team', args=[self.id])

    def get_invite_url(self):
        return urlresolvers.reverse('teams:join', args=[self.invite_hash])
