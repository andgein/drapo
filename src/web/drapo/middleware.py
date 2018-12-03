from django.utils import translation, deprecation
from django.conf import settings
import logging
import time

DRAPO_REQUEST_LOG_FORMAT = \
    '{request.method} {full_path} uid={user.id} uname={user.username} ip={remote_addr} ' \
    'sid={session_key!r} agent={user_agent!r} code={status_code} time_in_django_ms={response_time_ms}'

class LocaleMiddleware(deprecation.MiddlewareMixin):
    """
    This is a very simple middleware that parses a request
    and decides what translation object to install in the current
    thread context. This allows pages to be dynamically
    translated to the language the user desires (if the language
    is available, of course).
    """

    def process_request(self, request):
        language = translation.get_language_from_request(request)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

    def process_response(self, request, response):
        translation.deactivate()
        return response


def log_requests_middleware(get_response):
    """
    Middleware, that logs as much information as it can from request,
    including session id, user id and name, user agent, ip, time request took, etc.
    """
    logger = logging.getLogger('drapo.requests')
    format_str = getattr(settings, 'DRAPO_REQUEST_LOG_FORMAT', DRAPO_REQUEST_LOG_FORMAT)

    def middleware(request):
        start = time.perf_counter()
        response = get_response(request)
        end = time.perf_counter()
        response_time_ms = int((end - start) * 1000)

        extra = {
            'request': request,
            'full_path': request.get_full_path(),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'remote_addr': request.META.get('REMOTE_ADDR'),
            'status_code': response.status_code,
            'user': request.user,
            'session_key' : request.COOKIES.get(settings.SESSION_COOKIE_NAME),
            'response_time_ms' : response_time_ms,
        }
        message = format_str.format(**extra)
        logger.info(message, extra=extra)
        return response

    return middleware
