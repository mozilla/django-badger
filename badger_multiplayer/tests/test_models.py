import logging

from django.conf import settings

from django.core.management import call_command
from django.db.models import loading

from django.http import HttpRequest
from django.test.client import Client

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.template.defaultfilters import slugify

from django.contrib.auth.models import User

from . import BadgerTestCase

import badger
import badger_multiplayer

from badger.models import (Award, Progress,
        BadgeAwardNotAllowedException,
        BadgeAlreadyAwardedException)

from badger_multiplayer.models import (Badge, Nomination,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)

from badger_test.models import GuestbookEntry


class BadgerMultiplayerBadgeTest(BadgerTestCase):

    def setUp(self):
        self.user_1 = self._get_user(username="user_1",
                email="user_1@example.com", password="user_1_pass")

    def tearDown(self):
        Nomination.objects.all().delete()
        Award.objects.all().delete()
        Badge.objects.all().delete()

    def test_nominate_badge(self):
        """Can nominate a user for a badge"""
        badge = self._get_badge()
        nominator = self._get_user(username="nominator",
                email="nominator@example.com", password="nomnom1")
        nominee = self._get_user(username="nominee",
                email="nominee@example.com", password="nomnom2")

        ok_(not badge.is_nominated_for(nominee))
        nomination = badge.nominate_for(nominator=nominator, nominee=nominee)
        ok_(badge.is_nominated_for(nominee))

    def test_approve_nomination(self):
        """A nomination can be approved"""
        nomination = self._create_nomination()

        ok_(not nomination.is_approved())
        nomination.approve_by(nomination.badge.creator)
        ok_(nomination.is_approved())

    def test_accept_nomination(self):
        """A nomination can be accepted"""
        nomination = self._create_nomination()

        ok_(not nomination.is_accepted())
        nomination.accept(nomination.nominee)
        ok_(nomination.is_accepted())

    def test_accept_nomination(self):
        """A nomination that is approved and accepted results in an award"""
        nomination = self._create_nomination()

        ok_(not nomination.badge.is_awarded_to(nomination.nominee))
        nomination.approve_by(nomination.badge.creator)
        nomination.accept(nomination.nominee)
        ok_(nomination.badge.is_awarded_to(nomination.nominee))

        ct = Award.objects.filter(nomination=nomination).count()
        eq_(1, ct, "There should be an award associated with the nomination")

    def test_disallowed_nomination_approval(self):
        """By default, only badge creator should be allowed to approve a
        nomination."""

        nomination = self._create_nomination()
        other_user = self._get_user(username="other")

        try:
            nomination = nomination.approve_by(other_user)
            ok_(False, "Nomination should not have succeeded")
        except NominationApproveNotAllowedException, e:
            ok_(True)

    def test_disallowed_nomination_accept(self):
        """By default, only nominee should be allowed to accept a
        nomination."""

        nomination = self._create_nomination()
        other_user = self._get_user(username="other")

        try:
            nomination = nomination.accept(other_user)
            ok_(False, "Nomination should not have succeeded")
        except NominationAcceptNotAllowedException, e:
            ok_(True)

    def _get_user(self, username="tester", email="tester@example.com",
            password="trustno1"):
        (user, created) = User.objects.get_or_create(username=username,
                defaults=dict(email=email))
        if created:
            user.set_password(password)
            user.save()
        return user

    def test_nomination_badge_already_awarded(self):
        """New nomination for an awarded unique badge cannot be created"""
        user = self._get_user()
        b = Badge.objects.create(slug='one-and-only', title='One and Only',
                unique=True, creator=user)

        n = b.nominate_for(user)
        n.accept(user)
        n.approve_by(user)

        try:
            n = Nomination.objects.create(badge=b, nominee=user)
            ok_(False, 'BadgeAlreadyAwardedException should have been raised')
        except BadgeAlreadyAwardedException, e:
            pass

        # Nominations stick around after award.
        eq_(1, Nomination.objects.filter(badge=b, nominee=user).count())

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
