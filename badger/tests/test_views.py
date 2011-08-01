import logging

from django.conf import settings

from django.http import HttpRequest
from django.test.client import Client

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

from badger.models import (Badge, Award, Nomination,
        BadgeAwardNotAllowedException,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)


class BadgerViewsTest(BadgerTestCase):

    def setUp(self):
        self.testuser = self._get_user()
        self.client = LocalizingClient()

    def tearDown(self):
        Nomination.objects.all().delete()
        Award.objects.all().delete()
        Badge.objects.all().delete()

    def test_detail(self):
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

    def _get_user(self, username="tester", email="tester@example.com",
            password="trustno1"):
        (user, created) = User.objects.get_or_create(username=username,
                defaults=dict(email=email))
        if created:
            user.set_password(password)
            user.save()
        return user
