# -*- coding: utf-8 -*-
from os.path import dirname
import logging
import time

try:
    from PIL import Image
except ImportError:
    import Image

from django.conf import settings

from django.core.management import call_command
from django.db.models import loading
from django.core.files.base import ContentFile
from django.http import HttpRequest
from django.utils import simplejson as json
from django.test.client import Client

from django.core import mail

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

try:
    from funfactory.urlresolvers import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

from . import BadgerTestCase, patch_settings

import badger
from badger.models import (Badge, Award, Nomination, Progress, DeferredAward,
        BadgeAwardNotAllowedException,
        BadgeAlreadyAwardedException,
        DeferredAwardGrantNotAllowedException,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException,
        NominationRejectNotAllowedException,
        SITE_ISSUER, slugify)

from badger_example.models import GuestbookEntry


BASE_URL = 'http://example.com'
BADGE_IMG_FN = "%s/fixtures/default-badge.png" % dirname(dirname(__file__))


class BadgerBadgeTest(BadgerTestCase):

    def test_get_badge(self):
        """Can create a badge"""
        badge = self._get_badge()

        eq_(slugify(badge.title), badge.slug)
        ok_(badge.created is not None)
        ok_(badge.modified is not None)
        eq_(badge.created.year, badge.modified.year)
        eq_(badge.created.month, badge.modified.month)
        eq_(badge.created.day, badge.modified.day)

    def test_unicode_slug(self):
        """Issue #124: django slugify function turns up blank slugs"""
        badge = self._get_badge()
        badge.title = u'弁護士バッジ（レプリカ）'
        badge.slug = ''
        img_data = open(BADGE_IMG_FN, 'r').read()
        badge.image.save('', ContentFile(img_data), True)
        badge.save()

        ok_(badge.slug != '')
        eq_(slugify(badge.title), badge.slug)

    def test_award_badge(self):
        """Can award a badge to a user"""
        badge = self._get_badge()
        user = self._get_user()

        ok_(not badge.is_awarded_to(user))
        badge.award_to(awardee=user, awarder=badge.creator)
        ok_(badge.is_awarded_to(user))

    def test_award_unique_duplication(self):
        """Only one award for a unique badge can be created"""
        user = self._get_user()
        b = Badge.objects.create(slug='one-and-only', title='One and Only',
                unique=True, creator=user)
        a = Award.objects.create(badge=b, user=user)

        # award_to should not trigger the exception by default
        b.award_to(awardee=user)

        try:
            b.award_to(awardee=user, raise_already_awarded=True)
            ok_(False, 'BadgeAlreadyAwardedException should have been raised')
        except BadgeAlreadyAwardedException:
            # The raise_already_awarded flag should raise the exception
            pass

        try:
            a = Award.objects.create(badge=b, user=user)
            ok_(False, 'BadgeAlreadyAwardedException should have been raised')
        except BadgeAlreadyAwardedException:
            # But, directly creating another award should trigger the exception
            pass

        eq_(1, Award.objects.filter(badge=b, user=user).count())


class BadgerOBITest(BadgerTestCase):

    def test_baked_award_image(self):
        """Award gets image baked with OBI assertion"""
        # Get the source for a sample badge image
        img_data = open(BADGE_IMG_FN, 'r').read()

        # Make a badge with a creator
        user_creator = self._get_user(username="creator")
        badge = self._get_badge(title="Badge with Creator",
                                creator=user_creator)
        badge.image.save('', ContentFile(img_data), True)

        # Get some users who can award any badge
        user_1 = self._get_user(username="superuser_1",
                                is_superuser=True)
        user_2 = self._get_user(username="superuser_2",
                                is_superuser=True)

        # Get some users who can receive badges
        user_awardee_1 = self._get_user(username="awardee_1")
        user_awardee_2 = self._get_user(username="awardee_1")

        # Try awarding the badge once with baking enabled and once without
        for enabled in (True, False):
            with patch_settings(BADGER_BAKE_AWARD_IMAGES=enabled):
                award_1 = badge.award_to(awardee=user_awardee_1)
                if not enabled:
                    ok_(not award_1.image)
                else:
                    ok_(award_1.image)
                    img = Image.open(award_1.image.file)
                    hosted_assertion_url = img.info['openbadges']
                    expected_url = '%s%s' % (
                        BASE_URL, reverse('badger.award_detail_json',
                                          args=(award_1.badge.slug,
                                                award_1.id)))
                    eq_(expected_url, hosted_assertion_url)
                award_1.delete()


class BadgerProgressTest(BadgerTestCase):

    def test_progress_badge_already_awarded(self):
        """New progress toward an awarded unique badge cannot be recorded"""
        user = self._get_user()
        b = Badge.objects.create(slug='one-and-only', title='One and Only',
                unique=True, creator=user)

        p = b.progress_for(user)
        p.update_percent(100)

        try:
            p = Progress.objects.create(badge=b, user=user)
            ok_(False, 'BadgeAlreadyAwardedException should have been raised')
        except BadgeAlreadyAwardedException:
            pass

        # None, because award deletes progress.
        eq_(0, Progress.objects.filter(badge=b, user=user).count())


class BadgerDeferredAwardTest(BadgerTestCase):

    def test_claim_by_code(self):
        """Can claim a deferred award by claim code"""
        user = self._get_user()
        awardee = self._get_user(username='winner1',
                                 email='winner@example.com')

        badge1 = self._get_badge(title="Test A", creator=user)

        ok_(not badge1.is_awarded_to(awardee))

        da = DeferredAward(badge=badge1)
        da.save()
        code = da.claim_code

        eq_(1, DeferredAward.objects.filter(claim_code=code).count())
        DeferredAward.objects.claim_by_code(awardee, code)
        eq_(0, DeferredAward.objects.filter(claim_code=code).count())

        ok_(badge1.is_awarded_to(awardee))

        # Ensure the award was marked with the claim code.
        award = Award.objects.get(claim_code=code)
        eq_(award.badge.pk, badge1.pk)

    def test_claim_by_email(self):
        """Can claim all deferred awards by email address"""
        deferred_email = 'winner@example.com'
        user = self._get_user()
        titles = ("Test A", "Test B", "Test C")
        badges = (self._get_badge(title=title, creator=user)
                  for title in titles)
        deferreds = []

        # Issue deferred awards for each of the badges.
        for badge in badges:
            result = badge.award_to(email=deferred_email, awarder=user)
            deferreds.append(result)
            ok_(hasattr(result, 'claim_code'))

        # Scour the mail outbox for claim messages.
        if notification:
            for deferred in deferreds:
                found = False
                for msg in mail.outbox:
                    if (deferred.badge.title in msg.subject and
                            deferred.get_claim_url() in msg.body):
                        found = True
                ok_(found, '%s should have been found in subject' %
                           deferred.badge.title)

        # Register an awardee user with the email address, but the badge should
        # not have been awarded yet.
        awardee = self._get_user(username='winner2', email=deferred_email)
        for badge in badges:
            ok_(not badge.is_awarded_to(awardee))

        # Now, claim the deferred awards, and they should all self-destruct
        eq_(3, DeferredAward.objects.filter(email=awardee.email).count())
        DeferredAward.objects.claim_by_email(awardee)
        eq_(0, DeferredAward.objects.filter(email=awardee.email).count())

        # After claiming, the awards should exist.
        for badge in badges:
            ok_(badge.is_awarded_to(awardee))

    def test_reusable_claim(self):
        """Can repeatedly claim a reusable deferred award"""
        user = self._get_user()
        awardee = self._get_user(username='winner1',
                                 email='winner@example.com')

        badge1 = self._get_badge(title="Test A", creator=user, unique=False)

        ok_(not badge1.is_awarded_to(awardee))

        da = DeferredAward(badge=badge1, reusable=True)
        da.save()
        code = da.claim_code

        for i in range(0, 5):
            eq_(1, DeferredAward.objects.filter(claim_code=code).count())
            DeferredAward.objects.claim_by_code(awardee, code)

        ok_(badge1.is_awarded_to(awardee))
        eq_(5, Award.objects.filter(badge=badge1, user=awardee).count())

    def test_disallowed_claim(self):
        """Deferred award created by someone not allowed to award a badge
        cannot be claimed"""
        user = self._get_user()
        random_guy = self._get_user(username='random_guy',
                                    is_superuser=False)
        awardee = self._get_user(username='winner1',
                                 email='winner@example.com')

        badge1 = self._get_badge(title="Test A", creator=user)

        ok_(not badge1.is_awarded_to(awardee))

        da = DeferredAward(badge=badge1, creator=random_guy)
        da.save()
        code = da.claim_code

        eq_(1, DeferredAward.objects.filter(claim_code=code).count())
        result = DeferredAward.objects.claim_by_code(awardee, code)
        eq_(0, DeferredAward.objects.filter(claim_code=code).count())

        ok_(not badge1.is_awarded_to(awardee))

    def test_granted_claim(self):
        """Reusable deferred award can be granted to someone by email"""

        # Assemble the characters involved...
        creator = self._get_user()
        random_guy = self._get_user(username='random_guy',
                                    email='random_guy@example.com',
                                    is_superuser=False)
        staff_person = self._get_user(username='staff_person',
                                      email='staff@example.com',
                                      is_staff=True)
        grantee_email = 'winner@example.com'
        grantee = self._get_user(username='winner1',
                                 email=grantee_email)

        # Create a consumable award claim
        badge1 = self._get_badge(title="Test A", creator=creator)
        original_email = 'original@example.com'
        da = DeferredAward(badge=badge1, creator=creator, email=original_email)
        claim_code = da.claim_code
        da.save()

        # Grant the deferred award, ensure the existing one is modified.
        new_da = da.grant_to(email=grantee_email, granter=staff_person)
        ok_(claim_code != new_da.claim_code)
        ok_(da.email != original_email)
        eq_(da.pk, new_da.pk)
        eq_(new_da.email, grantee_email)

        # Claim the deferred award, assert that the appropriate deferred award
        # was destroyed
        eq_(1, DeferredAward.objects.filter(pk=da.pk).count())
        eq_(1, DeferredAward.objects.filter(pk=new_da.pk).count())
        DeferredAward.objects.claim_by_email(grantee)
        eq_(0, DeferredAward.objects.filter(pk=da.pk).count())
        eq_(0, DeferredAward.objects.filter(pk=new_da.pk).count())

        # Finally, assert the award condition
        ok_(badge1.is_awarded_to(grantee))

        # Create a reusable award claim
        badge2 = self._get_badge(title="Test B", creator=creator)
        da = DeferredAward(badge=badge2, creator=creator, reusable=True)
        claim_code = da.claim_code
        da.save()

        # Grant the deferred award, ensure a new deferred award is generated.
        new_da = da.grant_to(email=grantee_email, granter=staff_person)
        ok_(claim_code != new_da.claim_code)
        ok_(da.pk != new_da.pk)
        eq_(new_da.email, grantee_email)

        # Claim the deferred award, assert that the appropriate deferred award
        # was destroyed
        eq_(1, DeferredAward.objects.filter(pk=da.pk).count())
        eq_(1, DeferredAward.objects.filter(pk=new_da.pk).count())
        DeferredAward.objects.claim_by_email(grantee)
        eq_(1, DeferredAward.objects.filter(pk=da.pk).count())
        eq_(0, DeferredAward.objects.filter(pk=new_da.pk).count())

        # Finally, assert the award condition
        ok_(badge2.is_awarded_to(grantee))

        # Create one more award claim
        badge3 = self._get_badge(title="Test C", creator=creator)
        da = DeferredAward(badge=badge3, creator=creator)
        claim_code = da.claim_code
        da.save()

        # Grant the deferred award, ensure a new deferred award is generated.
        try:
            new_da = da.grant_to(email=grantee_email, granter=random_guy)
            is_ok = False
        except Exception, e:
            ok_(type(e) is DeferredAwardGrantNotAllowedException)
            is_ok = True

        ok_(is_ok, "Permission should be required for granting")

    def test_mass_generate_claim_codes(self):
        """Claim codes can be generated in mass for a badge"""
        # Assemble the characters involved...
        creator = self._get_user()
        random_guy = self._get_user(username='random_guy',
                                    email='random_guy@example.com',
                                    is_superuser=False)
        staff_person = self._get_user(username='staff_person',
                                      email='staff@example.com',
                                      is_staff=True)

        # Create a consumable award claim
        badge1 = self._get_badge(title="Test A", creator=creator)
        eq_(0, len(badge1.claim_groups))

        # Generate a number of groups of varying size
        num_awards = (10, 20, 40, 80, 100)
        num_groups = len(num_awards)
        groups_generated = dict()
        for x in range(0, num_groups):
            num = num_awards[x]
            cg = badge1.generate_deferred_awards(user=creator, amount=num)
            time.sleep(1.0)
            groups_generated[cg] = num
            eq_(num, DeferredAward.objects.filter(claim_group=cg).count())

        # Ensure the expected claim groups are available
        if False:
            # FIXME: Seems like the claim groups count doesn't work with
            # sqlite3 tests
            eq_(num_groups, len(badge1.claim_groups))
            for item in badge1.claim_groups:
                cg = item['claim_group']
                eq_(groups_generated[cg], item['count'])

            # Delete deferred awards found in the first claim group
            cg_1 = badge1.claim_groups[0]['claim_group']
            badge1.delete_claim_group(user=creator, claim_group=cg_1)

            # Assert that the claim group is gone, and now there's one less.
            eq_(num_groups - 1, len(badge1.claim_groups))

    def test_deferred_award_unique_duplication(self):
        """Only one deferred award for a unique badge can be created"""
        deferred_email = 'winner@example.com'
        user = self._get_user()
        b = Badge.objects.create(slug='one-and-only', title='One and Only',
                                 unique=True, creator=user)
        a = Award.objects.create(badge=b, user=user)

        b.award_to(email=deferred_email, awarder=user)

        # There should be one deferred award for the email.
        eq_(1, DeferredAward.objects.filter(email=deferred_email).count())

        # Award again. Tt should raise an exception and there still should
        # be one deferred award.
        self.assertRaises(
            BadgeAlreadyAwardedException,
            lambda: b.award_to(email=deferred_email, awarder=user))
        eq_(1, DeferredAward.objects.filter(email=deferred_email).count())

    def test_only_first_deferred_sends_email(self):
        """Only the first deferred award will trigger an email."""
        deferred_email = 'winner@example.com'
        user = self._get_user()
        b1 = Badge.objects.create(slug='one-and-only', title='One and Only',
                                  unique=True, creator=user)
        b1.award_to(email=deferred_email, awarder=user)

        # There should be one deferred award and one email in the outbox.
        eq_(1, DeferredAward.objects.filter(email=deferred_email).count())
        eq_(1, len(mail.outbox))

        # Award a second badge and there should be two deferred awards and
        # still only one email in the outbox.
        b2 = Badge.objects.create(slug='another-one', title='Another One',
                                  unique=True, creator=user)
        b2.award_to(email=deferred_email, awarder=user)
        eq_(2, DeferredAward.objects.filter(email=deferred_email).count())
        eq_(1, len(mail.outbox))


class BadgerMultiplayerBadgeTest(BadgerTestCase):

    def setUp(self):
        self.user_1 = self._get_user(username="user_1",
                email="user_1@example.com", password="user_1_pass")

        self.stranger = self._get_user(username="stranger",
                email="stranger@example.com",
                password="stranger_pass")

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

        eq_(False, nomination.allows_approve_by(self.stranger))
        eq_(True, nomination.allows_approve_by(nomination.badge.creator))

        ok_(not nomination.is_approved)
        nomination.approve_by(nomination.badge.creator)
        ok_(nomination.is_approved)

    def test_autoapprove_nomination(self):
        """All nominations should be auto-approved for a badge flagged for
        auto-approval"""
        badge = self._get_badge()
        badge.nominations_autoapproved = True
        badge.save()

        nomination = self._create_nomination()
        ok_(nomination.is_approved)

    def test_accept_nomination(self):
        """A nomination can be accepted"""
        nomination = self._create_nomination()

        eq_(False, nomination.allows_accept(self.stranger))
        eq_(True, nomination.allows_accept(nomination.nominee))

        ok_(not nomination.is_accepted)
        nomination.accept(nomination.nominee)
        ok_(nomination.is_accepted)

    def test_approve_accept_nomination(self):
        """A nomination that is approved and accepted results in an award"""
        nomination = self._create_nomination()

        ok_(not nomination.badge.is_awarded_to(nomination.nominee))
        nomination.approve_by(nomination.badge.creator)
        nomination.accept(nomination.nominee)
        ok_(nomination.badge.is_awarded_to(nomination.nominee))

        ct = Award.objects.filter(nomination=nomination).count()
        eq_(1, ct, "There should be an award associated with the nomination")

    def test_reject_nomination(self):
        SAMPLE_REASON = "Just a test anyway"
        nomination = self._create_nomination()
        rejected_by = nomination.badge.creator

        eq_(False, nomination.allows_reject_by(self.stranger))
        eq_(True, nomination.allows_reject_by(nomination.badge.creator))
        eq_(True, nomination.allows_reject_by(nomination.nominee))

        nomination.reject_by(rejected_by, reason=SAMPLE_REASON)
        eq_(rejected_by, nomination.rejected_by)
        ok_(nomination.is_rejected)
        eq_(SAMPLE_REASON, nomination.rejected_reason)

        eq_(False, nomination.allows_reject_by(self.stranger))
        eq_(False, nomination.allows_reject_by(nomination.badge.creator))
        eq_(False, nomination.allows_reject_by(nomination.nominee))
        eq_(False, nomination.allows_accept(self.stranger))
        eq_(False, nomination.allows_accept(nomination.nominee))
        eq_(False, nomination.allows_approve_by(self.stranger))
        eq_(False, nomination.allows_approve_by(nomination.badge.creator))

    def test_disallowed_nomination_approval(self):
        """By default, only badge creator should be allowed to approve a
        nomination."""

        nomination = self._create_nomination()
        other_user = self._get_user(username="other")

        try:
            nomination = nomination.approve_by(other_user)
            ok_(False, "Nomination should not have succeeded")
        except NominationApproveNotAllowedException:
            ok_(True)

    def test_disallowed_nomination_accept(self):
        """By default, only nominee should be allowed to accept a
        nomination."""

        nomination = self._create_nomination()
        other_user = self._get_user(username="other")

        try:
            nomination = nomination.accept(other_user)
            ok_(False, "Nomination should not have succeeded")
        except NominationAcceptNotAllowedException:
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
        except BadgeAlreadyAwardedException:
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
