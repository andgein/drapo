from django.template import Library
from django.utils import timezone
import datetime

register = Library()


@register.filter
def utcoffset(value):
    # Yeap, it's strange, but tags are so ugly.. So I defined not use value, but get current timezone from utils
    tz = timezone.get_current_timezone()
    return datetime.datetime.now(tz).utcoffset()
