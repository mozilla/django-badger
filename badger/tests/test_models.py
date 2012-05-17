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

from django.template.defaultfilters import slugify

try:
    from funfactory.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

from . import BadgerTestCase

import badger

from badger.models import (Badge, Award, Progress, DeferredAward,
        BadgeAwardNotAllowedException,
        BadgeAlreadyAwardedException,
        DeferredAwardGrantNotAllowedException,
        SITE_ISSUER)

from badger.tests.badger_example.models import GuestbookEntry


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

        # award_to should not trigger the exception
        b.award_to(awardee=user)

        try:
            a = Award.objects.create(badge=b, user=user)
            ok_(False, 'BadgeAlreadyAwardedException should have been raised')
        except BadgeAlreadyAwardedException, e:
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
        user_1 = self._get_user(username="superuser_1", is_superuser=True)
        user_2 = self._get_user(username="superuser_2", is_superuser=True)

        # Get some users who can receive badges
        user_awardee_1 = self._get_user(username="awardee_1")
        user_awardee_2 = self._get_user(username="awardee_1")

        # Award a badge, and try to extract the badge assertion baked in
        award_1 = badge.award_to(awardee=user_awardee_1)
        ok_(award_1.image)
        img = Image.open(award_1.image.file)

        hosted_assertion_url = img.info['openbadges']
        expected_url = '%s%s' % (
            BASE_URL, reverse('badger.award_detail_json',
                              args=(award_1.badge.slug, award_1.id)))
        eq_(expected_url, hosted_assertion_url)

        return True

        # TODO: Re-enable the testing below, if/when we go back to baking JSON
        # rather than hosted assertion URLs.

        assertion = json.loads(img.info['openbadges'])

        # Check the top-level award assertion data
        eq_(award_1.user.email, assertion['recipient'])
        eq_('%s%s' % (BASE_URL, award_1.get_absolute_url()),
            assertion['evidence'])

        # Check some of the badge details in the assertion
        a_badge = assertion['badge']
        eq_('0.5.0', a_badge['version'])
        eq_(badge.title, a_badge['name'])
        eq_(badge.description, a_badge['description'])
        eq_('%s%s' % (BASE_URL, badge.get_absolute_url()),
            a_badge['criteria'])

        # Check the badge issuer details
        b_issuer = a_badge['issuer']
        eq_(badge.creator.username, b_issuer['name'])
        eq_(badge.creator.email, b_issuer['contact'])
        eq_('%s%s' % (BASE_URL, badge.creator.get_absolute_url()),
            b_issuer['origin'])

        # Award a badge, and check that the awarder appears as issuer
        award_2 = badge.award_to(awardee=user_awardee_2, awarder=user_1)
        ok_(award_2.image)
        img = Image.open(award_2.image.file)
        assertion = json.loads(img.info['openbadges'])
        b_issuer = assertion['badge']['issuer']
        eq_(user_1.username, b_issuer['name'])
        eq_(user_1.email, b_issuer['contact'])
        eq_(BASE_URL, b_issuer['origin'])

        # Make a badge with no creator
        badge_no_creator = self._get_badge(title="Badge no Creator",
                                           creator=False)
        badge_no_creator.image.save('', ContentFile(img_data), True)

        # Award a badge, and check that the site issuer is used
        award_3 = badge_no_creator.award_to(awardee=user_awardee_1)
        ok_(award_3.image)
        img = Image.open(award_3.image.file)
        assertion = json.loads(img.info['openbadges'])
        b_issuer = assertion['badge']['issuer']
        eq_(SITE_ISSUER['name'], b_issuer['name'])
        eq_(SITE_ISSUER['contact'], b_issuer['contact'])
        eq_(SITE_ISSUER['origin'], b_issuer['origin'])


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
        except BadgeAlreadyAwardedException, e:
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
        eq_(num_groups, len(badge1.claim_groups))
        for item in badge1.claim_groups:
            cg = item['claim_group']
            eq_(groups_generated[cg], item['count'])

        # Delete deferred awards found in the first claim group
        cg_1 = badge1.claim_groups[0]['claim_group']
        badge1.delete_claim_group(user=creator, claim_group=cg_1)

        # Assert that the claim group is gone, and now there's one less.
        eq_(num_groups - 1, len(badge1.claim_groups))
