from django.template import Library

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
