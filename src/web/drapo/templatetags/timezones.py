from django.template import Library
from django.utils import timezone
import datetime

register = Library()


@register.filter
def utcoffset(value):
    # Yeap, it's strange, but tags are so ugly.. So I defined not use value, but get current timezone from utils
    tz = timezone.get_current_timezone()
    utc_offset = datetime.datetime.now(tz).utcoffset()

    minutes = (utc_offset.days * 24 * 60) + (utc_offset.seconds / 60)
    if minutes == 0:
        return ''
    return '(UTC%+03i:%02i)' % divmod(minutes, 60)
