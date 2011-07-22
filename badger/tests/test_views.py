import logging

from django.conf import settings

from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

from commons import LocalizingClient

from pyquery import PyQuery as pq

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.template.defaultfilters import slugify

from django.contrib.auth.models import User

from commons.urlresolvers import reverse

from badger.models import (Badge, Award, Nomination,
        BadgeAwardNotAllowedException,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)


class BadgerViewsTest(TestCase):

    def setUp(self):
        self.testuser = self._get_user()
        self.client = LocalizingClient()

    def tearDown(self):
        pass

    def test_view_create_badge_form(self):
        """Can view create badge form"""
        # Login should be required
        r = self.client.get(reverse('badger_create_badge'))
        eq_(302, r.status_code)
        ok_('/accounts/login' in r['Location'])

        # Should be fine after login
        self.client.login(username="tester", password="trustno1")
        r = self.client.get(reverse('badger_create_badge'))
        eq_(200, r.status_code)

        # Make a chick check for expected form elements
        doc = pq(r.content)

        form = doc('form#create_badge')
        eq_(1, form.length)

        eq_(1, form.find('input[name=title]').length)
        eq_(1, form.find('textarea[name=description]').length)
        # For styling purposes, we'll allow either an input or button element
        eq_(1, form.find('input.submit,button.submit').length)

    def _get_user(self, username="tester", email="tester@example.com",
            password="trustno1"):
        (user, created) = User.objects.get_or_create(username=username,
                defaults=dict(email=email))
        if created:
            user.set_password(password)
            user.save()
        return user
