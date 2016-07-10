import os.path
import string
import random

import django

from drapo.common import generate_random_secret_string
from . import settings


def _ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    else:
        if not os.path.isdir(path):
            raise Exception('Drapo: %s is not a directory' % path)


def save_uploaded_file(uploaded_file, directory, extension=None):
    DEFAULT_EXTENSION = ''

    if not os.path.isabs(directory):
        directory = os.path.join(settings.DRAPO_UPLOAD_DIR, directory)
    _ensure_directory_exists(directory)

    file_name = os.path.join(directory, generate_random_secret_string())
    if extension is None:
        extension = DEFAULT_EXTENSION
    if extension != '':
        file_name += '.' + extension

    with open(file_name, 'wb') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return file_name
