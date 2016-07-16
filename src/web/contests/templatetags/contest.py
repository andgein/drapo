from django.template import Library

register = Library()


@register.filter
def is_user_participating(contest, user):
    return user.is_authenticated() and contest.is_user_participating(user)


@register.filter
def get_participant_for(contest, user):
    return contest.get_participant_for_user(user)