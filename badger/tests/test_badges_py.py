import logging

from django.conf import settings
from django.core.management import call_command
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from . import BadgerTestCase

import badger
import badger_test
import badger_test.badges

from badger.models import (Badge, Award, Nomination, Progress,
        BadgeAwardNotAllowedException,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)

from badger_test.models import GuestbookEntry


class BadgesPyTest(BadgerTestCase):

    def setUp(self):
        self.user_1 = self._get_user(username="user_1",
                email="user_1@example.com", password="user_1_pass")

    def tearDown(self):
        Nomination.objects.all().delete()
        Award.objects.all().delete()
        Badge.objects.all().delete()

    def test_badges_from_fixture(self):
        """Badges can be created via fixture"""
        b1 = Badge.objects.get(slug="test-1")
        eq_("Test #1", b1.title)
        b2 = Badge.objects.get(slug="button-clicker")
        eq_("Button Clicker", b2.title)
        b3 = Badge.objects.get(slug="first-post")
        eq_("First post!", b3.title)

    def test_badges_from_code(self):
        """Badges can be created in code"""
        b1 = Badge.objects.get(slug="test-2")
        eq_("Test #2", b1.title)
        b2 = Badge.objects.get(slug="100-words")
        eq_("100 Words", b2.title)
        b3 = Badge.objects.get(slug="master-badger")
        eq_("Master Badger", b3.title)

    def test_badge_awarded_on_model_create(self):
        """A badge should be awarded on first guestbook post"""
        user = self._get_user()
        post = GuestbookEntry(message="This is my first post", creator=user)
        post.save()
        b = Badge.objects.get(slug='first-post')
        ok_(b.is_awarded_to(user))

    @attr('content')
    def test_badge_awarded_on_content(self):
        """A badge should be awarded upon 100 words worth of guestbook posts
        created"""
        user = self._get_user()
        
        b = Badge.objects.get(slug="100-words")

        # Post 5 words in progress...
        GuestbookEntry.objects.create(creator=user,
            message="A few words to start")
        ok_(not b.is_awarded_to(user))
        eq_(5, badger.progress('100-words', user).counter)

        # Post 5 more words in progress...
        GuestbookEntry.objects.create(creator=user,
            message="A few more words posted")
        ok_(not b.is_awarded_to(user))
        eq_(10, badger.progress('100-words', user).counter)

        # Post the other 90 in one burst...
        msg = ' '.join('lots of words that repeat' for x in range(18))
        GuestbookEntry.objects.create(creator=user, message=msg)

        # Should result in a badge award and reset progress.
        ok_(b.is_awarded_to(user))
        eq_(0, badger.progress('100-words', user).counter)

        # But, just checking the reset counter shouldn't create a new DB row.
        eq_(0, Progress.objects.filter(user=user, badge=b).count())

    def test_metabadge_awarded(self):
        """(TODO) Upon completing collection of badges, award a meta-badge"""
        user = self._get_user()
        Badge.objects.get(slug='test-1').award_to(user)
        Badge.objects.get(slug='test-2').award_to(user)
        Badge.objects.get(slug='button-clicker').award_to(user)

        b = Badge.objects.get(slug='master-badger')
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
