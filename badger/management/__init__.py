from os.path import dirname, basename

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_apps, get_models, signals
from django.utils.importlib import import_module

import badger


def update_badges():
    from django.utils.importlib import import_module

    for app in settings.INSTALLED_APPS:
        try:
            badges_mod = import_module('%s.badges' % app)
        except ImportError:
            continue
        call_command('loaddata', '%s_badges' % app, verbosity=0) 
        badges_mod.update_badges()


signals.post_syncdb.connect(lambda *args, **kwargs: update_badges(),
                            sender=badger.models)
