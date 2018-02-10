from django.core.management.base import BaseCommand, CommandError
from users.models import User
from contests.models import Contest, IndividualParticipant

import yaml


class Command(BaseCommand):
    help = 'Creates users from file and registers them to contest'

    def add_arguments(self, parser):
        parser.add_argument('contest_id', type=int)
        parser.add_argument('filename', type=str)

    def handle(self, *args, **options):
        contest_id = options['contest_id']
        try:
            contest = Contest.objects.get(pk=contest_id)
        except Contest.DoesNotExist:
            raise CommandError('Contest "%s" does not exist' % contest_id)

        with open(options['filename'], encoding='utf-8') as file:
            participants = yaml.load(file)

        for p in participants:
            user = User.objects.create_user(
                username=p['username'],
                email=p['email'],
                first_name=p['first_name'],
                last_name=p['last_name'],
                password=p['password']
            )
            user.save()

            IndividualParticipant(
                contest=contest,
                user=user,
                is_approved=True,
            ).save()

            self.stdout.write(self.style.SUCCESS('Registered user %s to contest' % p['username']))
