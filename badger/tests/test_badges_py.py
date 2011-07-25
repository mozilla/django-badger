import logging

from django.conf import settings
from django.core.management import call_command
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from . import TestCase

import badger
import badger_test
import badger_test.badges

from badger.models import (Badge, Award, Nomination,
        BadgeAwardNotAllowedException,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)

from badger_test.models import GuestbookEntry


class BadgesPyTest(TestCase):

    def setUp(self):
        self.user_1 = self._get_user(username="user_1",
                email="user_1@example.com", password="user_1_pass")

    def tearDown(self):
        Nomination.objects.all().delete()
        Award.objects.all().delete()
        Badge.objects.all().delete()

    def test_badges_from_fixture(self):
        """Badges should be created from fixture"""
        b1 = Badge.objects.get(slug="test-1")
        eq_("Test #1", b1.title)
        b2 = Badge.objects.get(slug="button-clicker")
        eq_("Button Clicker", b2.title)
        b3 = Badge.objects.get(slug="first-post")
        eq_("First post!", b3.title)

    def test_badge_awarded_on_model_create(self):
        """A badge should be awarded on first guestbook post"""
        user = self._get_user()
        post = GuestbookEntry(message="This is my first post", creator=user)
        post.save()
        b = Badge.objects.get(slug='first-post')
        ok_(b.is_awarded_to(user))

    def _get_user(self, username="tester", email="tester@example.com",
            password="trustno1"):
        (user, created) = User.objects.get_or_create(username=username,
                defaults=dict(email=email))
        if created:
            user.set_password(password)
            user.save()
        return user

    def _get_badge(self, title="Test Badge",
            description="This is a test badge", creator=None):
        creator = creator or self.user_1
        (badge, created) = Badge.objects.get_or_create(title=title,
                defaults=dict(description=description, creator=creator))
        return badge

    def _create_nomination(self, badge=None, nominator=None, nominee=None):
        badge = badge or self._get_badge()
        nominator = nominator or self._get_user(username="nominator",
                email="nominator@example.com", password="nomnom1")
        nominee = nominee or self._get_user(username="nominee",
                email="nominee@example.com", password="nomnom2")
        nomination = badge.nominate_for(nominator=nominator, nominee=nominee)
        return nomination
