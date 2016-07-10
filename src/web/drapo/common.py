import mimetypes
import os
import string
import urllib.parse

from django.utils import crypto
from django.http import HttpResponse
from django.http.response import HttpResponseNotFound


def generate_random_secret_string(length=12, allowed_chars=string.ascii_lowercase):
    return crypto.get_random_string(length, allowed_chars)


def respond_as_attachment(request, file_path, original_filename, content_type=None, encoding=None):
    if not os.path.exists(file_path):
        return HttpResponseNotFound()

    with open(file_path, 'rb') as fp:
        response = HttpResponse(fp.read())

    if content_type is None:
        content_type, encoding = mimetypes.guess_type(original_filename)
    if content_type is None:
        content_type = 'application/octet-stream'
    response['Content-Type'] = content_type
    response['Content-Length'] = str(os.stat(file_path).st_size)
    if encoding is not None:
        response['Content-Encoding'] = encoding

    # To inspect details for the below code, see http://greenbytes.de/tech/tc2231/
    if 'WebKit' in request.META['HTTP_USER_AGENT']:
        # Safari 3.0 and Chrome 2.0 accepts UTF-8 encoded string directly.
        filename_header = 'filename=%s' % original_filename
    elif 'MSIE' in request.META['HTTP_USER_AGENT']:
        # IE does not support internationalized filename at all.
        # It can only recognize internationalized URL, so we do the trick via routing rules.
        filename_header = ''
    else:
        # For others like Firefox, we follow RFC2231 (encoding extension in HTTP headers).
        filename_header = 'filename*=UTF-8\'\'%s' % urllib.parse.quote(original_filename)
    response['Content-Disposition'] = 'attachment; ' + filename_header
    return response
