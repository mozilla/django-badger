import logging

from django.conf import settings

from django.http import HttpRequest
from django.test.client import Client

from django.utils import simplejson
from django.utils.translation import get_language

from django.contrib.auth.models import User

from pyquery import PyQuery as pq

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.template.defaultfilters import slugify

try:
    from funfactory.urlresolvers import (get_url_prefix, Prefixer, reverse,
                                         set_url_prefix)
    from tower import activate
except ImportError, e:
    from django.core.urlresolvers import reverse
    get_url_prefix = None

from . import BadgerTestCase

from badger.models import (Badge, Award, Progress, DeferredAward,
        BadgeAwardNotAllowedException)
from badger.utils import get_badge, award_badge


class BadgerViewsTest(BadgerTestCase):

    def setUp(self):
        self.testuser = self._get_user()
        self.client = Client()
        Award.objects.all().delete()

    def tearDown(self):
        Award.objects.all().delete()
        Badge.objects.all().delete()

    @attr('json')
    def test_badge_detail(self):
        """Can view badge detail"""
        user = self._get_user()
        badge = Badge(creator=user, title="Test II",
                      description="Another test")
        badge.save()

        r = self.client.get(reverse('badger.views.detail',
            args=(badge.slug,)), follow=True)
        doc = pq(r.content)

        eq_('badge_detail', doc.find('body').attr('id'))
        eq_(1, doc.find('.badge-title:contains("%s")' % badge.title).length)
        eq_(badge.description, doc.find('.badge .description').text())

        # Now, take a look at the JSON format
        url = reverse('badger.detail_json', args=(badge.slug, ))
        r = self.client.get(url, follow=True)

        data = simplejson.loads(r.content)
        eq_(badge.title, data['name'])
        eq_(badge.description, data['description'])
        eq_('http://testserver%s' % badge.get_absolute_url(), 
            data['criteria'])

    @attr('json')
    def test_award_detail(self):
        """Can view award detail"""
        user = self._get_user()
        user2 = self._get_user(username='tester2')

        b1, created = Badge.objects.get_or_create(creator=user,
                title="Code Badge #1", description="Some description")
        award = b1.award_to(user2)

        url = reverse('badger.views.award_detail', args=(b1.slug, award.pk,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_('award_detail', doc.find('body').attr('id'))
        eq_(1, doc.find('.awarded_to .username:contains("%s")' % user2.username).length)
        eq_(1, doc.find('.badge-title:contains("%s")' % b1.title).length)

        # Now, take a look at the JSON format
        url = reverse('badger.award_detail_json', args=(b1.slug, award.pk,))
        r = self.client.get(url, follow=True)

        data = simplejson.loads(r.content)
        eq_(award.user.email, data['recipient'])
        eq_('http://testserver%s' % award.get_absolute_url(), 
            data['evidence'])
        eq_(award.badge.title, data['badge']['name'])
        eq_(award.badge.description, data['badge']['description'])
        eq_('http://testserver%s' % award.badge.get_absolute_url(), 
            data['badge']['criteria'])

    def test_awards_by_user(self):
        """Can view awards by user"""
        user = self._get_user()
        user2 = self._get_user(username='tester2')

        b1, created = Badge.objects.get_or_create(creator=user, title="Code Badge #1")
        b2, created = Badge.objects.get_or_create(creator=user, title="Code Badge #2")
        b3, created = Badge.objects.get_or_create(creator=user, title="Code Badge #3")

        b1.award_to(user2)
        award_badge(b2.slug, user2)
        Award.objects.create(badge=b3, user=user2)

        url = reverse('badger.views.awards_by_user', args=(user2.username,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_('badge_awards_by_user', doc.find('body').attr('id'))
        eq_(3, doc.find('.badge').length)
        for b in (b1, b2, b3):
            eq_(1, doc.find('.badge .title:contains("%s")' % b.title).length)

    def test_awards_by_badge(self):
        """Can view awards by badge"""
        user = self._get_user()
        b1 = Badge.objects.create(creator=user, title="Code Badge #1")

        u1 = self._get_user(username='tester1')
        u2 = self._get_user(username='tester2')
        u3 = self._get_user(username='tester3')

        for u in (u1, u2, u3):
            b1.award_to(u)

        url = reverse('badger.views.awards_by_badge', args=(b1.slug,))
        r = self.client.get(url, follow=True)
        doc = pq(r.content)

        eq_(3, doc.find('.award').length)
        for u in (u1, u2, u3):
            eq_(1, doc.find('.award .user:contains("%s")' % u.username)
                      .length)

    def test_issue_award(self):
        """Badge creator can issue award to another user"""
        
        user1 = self._get_user(username="creator", email="creator@example.com")
        user2 = self._get_user(username="awardee", email="awardee@example.com")

        b1 = Badge.objects.create(creator=user1, title="Badge to awarded")

        url = reverse('badger.views.award_badge', args=(b1.slug,))

        # Non-creator should be denied attempt to award badge
        self.client.login(username="awardee", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(403, r.status_code)

        # But, the creator should be allowed
        self.client.login(username="creator", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        form = doc('form#award_badge')
        eq_(1, form.length)
        eq_(1, form.find('*[name=emails]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(url, dict(
            emails=user2.email,
        ), follow=False)

        ok_('award' in r['Location'])

        ok_(b1.is_awarded_to(user2))

    def test_issue_multiple_awards(self):
        """Multiple emails can be submitted at once to issue awards"""
        # Build creator user and badge
        creator = self._get_user(username="creator", email="creator@example.com")
        b1 = Badge.objects.create(creator=creator, title="Badge to defer")

        # Build future awardees
        user1 = self._get_user(username="user1", email="user1@example.com")
        user2 = self._get_user(username="user2", email="user2@example.com")
        user3 = self._get_user(username="user3", email="user3@example.com")
        user4_email = 'user4@example.com'

        # Login as the badge creator, prepare to award...
        self.client.login(username="creator", password="trustno1")
        url = reverse('badger.views.award_badge', args=(b1.slug,))
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        # Make sure the expected parts appear in the form.
        doc = pq(r.content)
        form = doc('form#award_badge')
        eq_(1, form.length)
        eq_(1, form.find('*[name=emails]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        # Post a list of emails with a variety of separators.
        r = self.client.post(url, dict(
            emails=("%s,%s\n%s %s" %
                    (user1.email, user2.email, user3.email, user4_email)),
        ), follow=False)

        # Ensure that the known users received awards and the unknown user got
        # a deferred award.
        ok_(b1.is_awarded_to(user1))
        ok_(b1.is_awarded_to(user2))
        ok_(b1.is_awarded_to(user3))
        eq_(1, DeferredAward.objects.filter(email=user4_email).count())

    def test_issue_deferred_award(self):
        """Deferred award for a badge can be issued to an email address."""
        deferred_email = "awardee@example.com"
        user1 = self._get_user(username="creator", email="creator@example.com")
        b1 = Badge.objects.create(creator=user1, title="Badge to defer")
        url = reverse('badger.views.award_badge', args=(b1.slug,))

        self.client.login(username="creator", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        form = doc('form#award_badge')
        eq_(1, form.length)
        eq_(1, form.find('*[name=emails]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(url, dict(
            emails=deferred_email,
        ), follow=False)

        ok_('award' not in r['Location'])

        user2 = self._get_user(username="awardee", email=deferred_email)
        self.client.login(username="awardee", password="trustno1")
        r = self.client.get(reverse('badger.views.detail',
            args=(b1.slug,)), follow=True)
        ok_(b1.is_awarded_to(user2))

    def test_grant_deferred_award(self):
        """Deferred award for a badge can be granted to an email address."""
        deferred_email = "awardee@example.com"
        user1 = self._get_user(username="creator", email="creator@example.com")
        b1 = Badge.objects.create(creator=user1, title="Badge to defer")
        
        da = DeferredAward(badge=b1, creator=user1, email='foobar@example.com')
        da.save()
        url = da.get_claim_url()

        self.client.login(username="creator", password="trustno1")
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        form = doc('form#grant_award')
        eq_(1, form.length)
        eq_(1, form.find('*[name=email]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(url, dict(
            is_grant=1, email=deferred_email,
        ), follow=False)

        user2 = self._get_user(username="awardee", email=deferred_email)
        self.client.login(username="awardee", password="trustno1")
        r = self.client.get(reverse('badger.views.detail',
            args=(b1.slug,)), follow=True)
        ok_(b1.is_awarded_to(user2))
