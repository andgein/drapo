import datetime

from django.template import Library
from django.utils.timezone import is_aware, utc


register = Library()


@register.filter
def is_user_participating(contest, user):
    return user.is_authenticated() and contest.is_user_participating(user)


@register.filter
def get_participant_for(contest, user):
    return contest.get_participant_for_user(user)


@register.filter
def is_started_for(contest, participant):
    return contest.is_started_for(participant)


@register.filter
def is_running_for(contest, participant):
    return contest.is_running_for(participant)


@register.filter
def is_finished_for(contest, participant):
    return contest.is_finished_for(participant)


@register.filter
def start_time_for(contest, participant):
    return contest.start_time_for(participant)


@register.filter
def finish_time_for(contest, participant):
    return contest.finish_time_for(participant)


@register.filter
def timesince_hhmm(d, now=None, reversed=False):
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        now = datetime.datetime.now(utc if is_aware(d) else None)

    delta = (d - now) if reversed else (now - d)
    since = max(delta.days * 24 * 60 * 60 + delta.seconds, 0)
    hours, minutes = divmod(since // 60, 60)
    return '{:02d}:{:02d}'.format(hours, minutes)
