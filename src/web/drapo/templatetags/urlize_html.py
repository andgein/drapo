from django import template
from django.template import Library
from django.conf import settings
from django.utils.html import urlize
from django.utils.safestring import mark_safe

register = Library()


@register.filter("urlize_html")
def urlize_html(html):
    """
    Returns urls found in an (X)HTML text node element as urls via Django urlize filter.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in urlize_html The Python BeautifulSoup libraries aren't installed.")
        return html
    else:
        soup = BeautifulSoup(html, 'html.parser')

        text_nodes = soup.find_all(text=True)
        for text_node in text_nodes:
            urlized_text = urlize(text_node)
            text_node.replace_with(BeautifulSoup(urlized_text, 'html.parser'))

        return mark_safe(str(soup))
