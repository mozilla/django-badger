from os.path import dirname, basename

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_apps, get_models, signals
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

import badger


def update_badges(overwrite=False):
    from django.utils.importlib import import_module

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            badges_mod = import_module('%s.badges' % app)
            call_command('loaddata', '%s_badges' % app, verbosity=0)
            badges_mod.update_badges(overwrite)
        except ImportError, e:
            if module_has_submodule(mod, 'badges'):
                raise


signals.post_syncdb.connect(lambda *args, **kwargs: update_badges(),
                            sender=badger.models)
