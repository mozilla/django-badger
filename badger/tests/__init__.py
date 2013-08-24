import logging

from contextlib import contextmanager

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.contrib.auth.models import User
from django import test
from django.utils.translation import get_language

try:
    from funfactory.urlresolvers import (get_url_prefix, Prefixer, reverse,
                                         set_url_prefix)
    from tower import activate
    from django.test.client import RequestFactory
except ImportError:
    from django.core.urlresolvers import reverse
    get_url_prefix = None

import badger

from badger.models import (Badge, Award, Progress, DeferredAward)


class SettingDoesNotExist:
    pass


@contextmanager
def patch_settings(**kwargs):
    """Contextmanager to temporarily change settings.
    See: http://stackoverflow.com/a/3519955"""
    from django.conf import settings
    old_settings = []
    del_settings = []
    for key, new_value in kwargs.items():
        old_value = getattr(settings, key, SettingDoesNotExist)
        old_settings.append((key, old_value))
        setattr(settings, key, new_value)
    yield
    for key, old_value in old_settings:
        if old_value is SettingDoesNotExist:
            delattr(settings, key)
        else:
            setattr(settings, key, old_value)


class BadgerTestCase(test.TestCase):
    """Ensure test app and models are set up before tests"""

    def _pre_setup(self):
        loading.cache.loaded = False
        call_command('update_badges', verbosity=0)
        badger.autodiscover()

        if get_url_prefix:
            # If we're in funfactoryland, make sure a locale prefix is
            # set for urlresolvers
            locale = 'en-US'
            self.old_prefix = get_url_prefix()
            self.old_locale = get_language()
            rf = RequestFactory()
            set_url_prefix(Prefixer(rf.get('/%s/' % (locale,))))

        # Create a default user for tests
        self.user_1 = self._get_user(username="user_1",
                                     email="user_1@example.com",
                                     password="user_1_pass")

        # Call the original method that does the fixtures etc.
        super(test.TestCase, self)._pre_setup()

    def _post_teardown(self):
        # Call the original method.
        super(test.TestCase, self)._post_teardown()

        Award.objects.all().delete()
        Badge.objects.all().delete()

        loading.cache.loaded = False

        if get_url_prefix:
            # If we're in funfactoryland, back out of the locale tweaks
            set_url_prefix(self.old_prefix)

    def _get_user(self, username="tester", email="tester@example.com",
            password="trustno1", is_staff=False, is_superuser=False):
        (user, created) = User.objects.get_or_create(username=username,
                defaults=dict(email=email))
        if created:
            user.is_superuser = is_superuser
            user.is_staff = is_staff
            user.set_password(password)
            user.save()
        return user

    def _get_badge(self, title="Test Badge",
            description="This is a test badge", creator=None, unique=True):
        if creator is None:
            creator = self.user_1
        elif creator is False:
            creator = None
        (badge, created) = Badge.objects.get_or_create(title=title,
                defaults=dict(description=description, creator=creator,
                              unique=unique))
        return badge
