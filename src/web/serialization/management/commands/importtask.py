import os
import yaml

from django.core.management import BaseCommand, CommandError

from serialization.models import DirectoryContext, Task


class Command(BaseCommand):
    help = 'Imports task from a yaml specification'

    def add_arguments(self, parser):
        parser.add_argument('--file', metavar='path', nargs='?', type=str, default=None)

    def handle(self, *args, **options):
        file = options['file']
        if file is None or not os.path.isfile(file):
            raise CommandError('Should specify an existing file with a spec')


        with open(file, 'rt', encoding='utf-8') as f:
            yaml_data = f.read()

        try:
            task = yaml.load(yaml_data)
        except Exception as e:
            raise CommandError('This is not a valid task specification:\n%s' % str(e))

        if not isinstance(task, Task):
            raise CommandError('This is not a task specification')

        context = DirectoryContext(os.path.dirname(file))
        task.to_model(context)
