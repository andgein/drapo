import os
from urllib.parse import urlparse

from django.core.management import BaseCommand, CommandError

from serialization.models import DirectoryContext
from serialization.utils import load_yaml_from_data, load_yaml_from_file

from requests import get


class Command(BaseCommand):
    help = 'Imports objects from a yaml specification'

    def add_arguments(self, parser):
        parser.add_argument('--file', metavar='path', nargs='?', type=str, default=None)

    def handle(self, *args, **options):
        file = options['file']
        try:
            parts = urlparse(file)
            if parts.scheme == 'http' or parts.scheme == 'https':
                data = get(file).text
                obj = load_yaml_from_data(data)
            elif parts.scheme == '':
                obj = load_yaml_from_file(file)
            else:
                raise RuntimeError("Unknown scheme: %s" % parts.scheme)
        except Exception as e:
            raise CommandError("Failed to load spec due to %s" % str(e))

        ctx = DirectoryContext(os.path.dirname(file))
        try:
            obj.to_model(ctx)
        except Exception as e:
            raise CommandError("Failed to import object, the following error occurred: %s" % str(e))
