import logging
import time

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from django.http import HttpRequest, HttpResponse
from django.utils import simplejson as json
from django.test.client import Client

from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser

from . import BadgerTestCase

import badger

from badger.models import (Badge, Award, Nomination, Progress, DeferredAward)
from badger.middleware import (RecentAwardsMiddleware,
                               LAST_AWARD_CHECK_COOKIE_NAME)


class RecentAwardsMiddlewareTest(BadgerTestCase):

    def setUp(self):
        self.creator = self._get_user(username='creator')
        self.testuser = self._get_user()
        self.mw = RecentAwardsMiddleware()

        self.badges = []
        for n in ('test1','test2','test3'):
            badge = Badge(title=n, creator=self.creator)
            badge.save()
            self.badges.append(badge)

        self.awards = []
        for b in self.badges:
            self.awards.append(b.award_to(self.testuser))

    def tearDown(self):
        Award.objects.all().delete()
        Badge.objects.all().delete()

    def test_anonymous(self):
        """No recent awards for anonymous user"""
        request = HttpRequest()
        request.user = AnonymousUser()
        self.mw.process_request(request)
        ok_(hasattr(request, 'recent_awards'))
        eq_(None, request.recent_awards)

    def test_no_cookie(self):
        """No recent awards without a last-check cookie, but set the cookie"""
        request = HttpRequest()
        request.user = self.testuser
        self.mw.process_request(request)
        ok_(hasattr(request, 'recent_awards'))
        eq_(None, request.recent_awards)

        response = HttpResponse()
        self.mw.process_response(request, response)
        ok_(LAST_AWARD_CHECK_COOKIE_NAME in response.cookies)

    def test_unused_recent_awards(self):
        """Recent awards offered with cookie, but cookie not updated if unused"""
        request = HttpRequest()
        request.user = self.testuser
        request.COOKIES[LAST_AWARD_CHECK_COOKIE_NAME] = '1156891591.492586'
        self.mw.process_request(request)
        ok_(hasattr(request, 'recent_awards'))

        response = HttpResponse()
        self.mw.process_response(request, response)
        ok_(LAST_AWARD_CHECK_COOKIE_NAME not in response.cookies)

    def test_used_recent_awards(self):
        """Recent awards offered with cookie, cookie updated if set used"""
        old_time = '1156891591.492586'
        request = HttpRequest()
        request.user = self.testuser
        request.COOKIES[LAST_AWARD_CHECK_COOKIE_NAME] = old_time
        self.mw.process_request(request)
        ok_(hasattr(request, 'recent_awards'))

        # Use the recent awards set by checking length and contents
        eq_(3, len(request.recent_awards))
        for ra in request.recent_awards:
            ok_(ra in self.awards)

        response = HttpResponse()
        self.mw.process_response(request, response)
        ok_(LAST_AWARD_CHECK_COOKIE_NAME in response.cookies)
        ok_(response.cookies[LAST_AWARD_CHECK_COOKIE_NAME].value != old_time)
