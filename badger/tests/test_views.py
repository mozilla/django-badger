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

from badger.models import (Badge, Award, Progress,
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
        eq_(badge.title, doc.find('.badge .title').text())
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
        eq_(1, doc.find('.badge .title:contains("%s")' % b1.title).length)

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
            eq_(1, doc.find('.badge .title:contains("%s")' % b.title)
                      .length)

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
        
        user1 = self._get_user(username="creator")
        user2 = self._get_user(username="awardee")

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
        eq_(1, form.find('*[name=user]').length)
        eq_(1, form.find('input.submit,button.submit').length)

        r = self.client.post(url, dict(
            user=user2.id,
        ), follow=False)

        ok_(b1.is_awarded_to(user2))
