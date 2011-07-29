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
        b = Badge.objects.get(slug="test-1")
        eq_("Test #1", b.title)
        b = Badge.objects.get(slug="button-clicker")
        eq_("Button Clicker", b.title)
        b = Badge.objects.get(slug="first-post")
        eq_("First post!", b.title)

    def test_badges_from_code(self):
        """Badges can be created in code"""
        b = Badge.objects.get(slug="test-2")
        eq_("Test #2", b.title)
        b = Badge.objects.get(slug="awesomeness")
        eq_("Awesomeness (you have it)", b.title)
        b = Badge.objects.get(slug="250-words")
        eq_("250 Words", b.title)
        b = Badge.objects.get(slug="master-badger")
        eq_("Master Badger", b.title)

    def test_badge_awarded_on_model_create(self):
        """A badge should be awarded on first guestbook post"""
        user = self._get_user()
        post = GuestbookEntry(message="This is my first post", creator=user)
        post.save()
        b = Badge.objects.get(slug='first-post')
        ok_(b.is_awarded_to(user))

    def test_badge_awarded_on_content(self):
        """A badge should be awarded upon 250 words worth of guestbook posts
        created"""
        user = self._get_user()

        b = badger.badge('250-words')

        # Post 5 words in progress...
        GuestbookEntry.objects.create(creator=user,
            message="A few words to start")
        ok_(not b.is_awarded_to(user))
        eq_(5, b.progress_for(user).counter)

        # Post 5 more words in progress...
        GuestbookEntry.objects.create(creator=user,
            message="A few more words posted")
        ok_(not b.is_awarded_to(user))
        eq_(10, b.progress_for(user).counter)

        # Post 90 more...
        msg = ' '.join('lots of words that repeat' for x in range(18))
        GuestbookEntry.objects.create(creator=user, message=msg)
        ok_(not b.is_awarded_to(user))
        eq_(100, b.progress_for(user).counter)

        # And 150 more for the finale...
        msg = ' '.join('lots of words that repeat' for x in range(30))
        GuestbookEntry.objects.create(creator=user, message=msg)

        # Should result in a badge award and reset progress.
        ok_(b.is_awarded_to(user))
        eq_(0, b.progress_for(user).counter)

        # But, just checking the reset counter shouldn't create a new DB row.
        eq_(0, Progress.objects.filter(user=user, badge=b).count())

    @attr('current')
    def test_badge_awarded_on_content_percent(self):
        """A badge should be awarded upon 250 words worth of guestbook posts
        created, but the tracking is done via percentage"""
        user = self._get_user()

        b = badger.badge('250-words-by-percent')

        # Post 5 words in progress...
        GuestbookEntry.objects.create(creator=user,
            message="A few words to start")
        ok_(not b.is_awarded_to(user))
        eq_((5.0 / 250.0) * 100.0, b.progress_for(user).percent)

        # Post 5 more words in progress...
        GuestbookEntry.objects.create(creator=user,
            message="A few more words posted")
        ok_(not b.is_awarded_to(user))
        eq_((10.0 / 250.0) * 100.0, b.progress_for(user).percent)

        # Post 90 more...
        msg = ' '.join('lots of words that repeat' for x in range(18))
        GuestbookEntry.objects.create(creator=user, message=msg)
        ok_(not b.is_awarded_to(user))
        eq_((100.0 / 250.0) * 100.0, b.progress_for(user).percent)

        # And 150 more for the finale...
        msg = ' '.join('lots of words that repeat' for x in range(30))
        GuestbookEntry.objects.create(creator=user, message=msg)

        # Should result in a badge award and reset progress.
        ok_(b.is_awarded_to(user))
        eq_(0, b.progress_for(user).percent)

        # But, just checking the reset percent shouldn't create a new DB row.
        eq_(0, Progress.objects.filter(user=user, badge=b).count())

    def test_metabadge_awarded(self):
        """(TODO) Upon completing collection of badges, award a meta-badge"""
        user = self._get_user()
        badger.award('test-1', user)
        badger.award('test-2', user)
        badger.award('awesomeness', user)
        badger.award('button-clicker', user)
        ok_(badger.badge('master-badger').is_awarded_to(user))

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
