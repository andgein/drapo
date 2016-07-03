from django.template import Library

register = Library()


@register.filter
def item(obj, index):
    return obj[index]


@register.filter
def attr(obj, attribute):
    return getattr(obj, attribute, '')


@register.filter
def has_item(obj, index):
    try:
        _ = obj[index]
        return True
    except KeyError:
        return False


@register.filter
def has_attr(obj, attribute):
    return hasattr(obj, attribute)
