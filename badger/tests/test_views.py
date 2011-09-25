import logging

from django.conf import settings

from django.http import HttpRequest
from django.test.client import Client

from django.utils import simplejson

from commons import LocalizingClient

from pyquery import PyQuery as pq

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.template.defaultfilters import slugify

from django.contrib.auth.models import User

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

from . import BadgerTestCase

from badger.models import (Badge, Award, Progress,
        BadgeAwardNotAllowedException)
from badger.utils import get_badge, award_badge


class BadgerViewsTest(BadgerTestCase):

    def setUp(self):
        self.testuser = self._get_user()
        self.client = LocalizingClient()
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

        b1, created = Badge.objects.get_or_create(creator=user, title="Code Badge #1")
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
        eq_(3, doc.find('.award').length)
        for b in (b1, b2, b3):
            eq_(1, doc.find('.award .badge .title:contains("%s")' % b.title)
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

        eq_('badge_awards_by_badge', doc.find('body').attr('id'))
        eq_(3, doc.find('.award').length)
        for u in (u1, u2, u3):
            eq_(1, doc.find('.award .username:contains("%s")' % u.username)
                      .length)

    def _get_user(self, username="tester", email="tester@example.com",
            password="trustno1"):
        (user, created) = User.objects.get_or_create(username=username,
                defaults=dict(email=email))
        if created:
            user.set_password(password)
            user.save()
        return user
