from os.path import dirname, basename

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_apps, get_models, signals
from django.utils.importlib import import_module

from badger.models import Badge, Award, Progress
from badger.management import update_badges


class Command(BaseCommand):
    args = ''
    help = 'Rebake award images'

    def handle(self, *args, **options):
        for award in Award.objects.all():
            award.save()
