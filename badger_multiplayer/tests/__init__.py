from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django import test

import badger


class BadgerTestCase(test.TestCase):
    """Ensure test app and models are set up before tests"""
    apps = ('badger_test', 'badger_multiplayer_test', )

    def _pre_setup(self):
        # Add the models to the db.
        self._original_installed_apps = list(settings.INSTALLED_APPS)
        for app in self.apps:
            settings.INSTALLED_APPS.append(app)
        loading.cache.loaded = False
        call_command('syncdb', interactive=False, verbosity=0)
        call_command('update_badges', verbosity=0)
        badger.autodiscover()
        # Call the original method that does the fixtures etc.
        super(test.TestCase, self)._pre_setup()

    def _post_teardown(self):
        # Call the original method.
        super(test.TestCase, self)._post_teardown()
        # Restore the settings.
        settings.INSTALLED_APPS = self._original_installed_apps
        loading.cache.loaded = False

