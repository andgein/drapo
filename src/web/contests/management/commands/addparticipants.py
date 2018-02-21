from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users.models import User
from contests.models import Contest, ContestRegion, IndividualParticipant

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

        with transaction.atomic():
            for p in participants:
                self.add_participant(p, contest)
                self.stdout.write(self.style.SUCCESS('Registered user %s to contest' % p['username']))

    def get_region(self, contest, region):
        if not region:
            return None
        if type(region) is int:
            return ContestRegion.objects.get(id=region, contest=contest)
        return ContestRegion.objects.get(name=region, contest=contest)

    def add_participant(self, p, contest):
        user, _ = User.objects.update_or_create(
            username=p['username'],
            defaults={
                'email': p['email'],
                'first_name': p['first_name'],
                'last_name': p['last_name'],
            }
        )
        user.set_password(p['password'])
        user.save()

        region = self.get_region(contest, p.get('region'))

        IndividualParticipant.objects.update_or_create(
            contest=contest,
            user=user,
            defaults={
                'is_approved': True,
                'region': region,
            }
        )

