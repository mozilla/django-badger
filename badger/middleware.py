import logging
import time
from datetime import datetime
from django.conf import settings

from .models import (Badge, Award)


LAST_AWARD_CHECK_COOKIE_NAME = getattr(settings,
    'BADGER_LAST_AWARD_CHECK_COOKIE_NAME', 'badgerLastAwardCheck')


class RecentAwardsList(object):

    def __init__(self, request):
        self.request = request
        self.was_used = False
        self._queryset = None

    @property
    def recent_awards(self):
        if not self._queryset:
            try:
                c_name = LAST_AWARD_CHECK_COOKIE_NAME
                last_check = float(self.request.COOKIES[c_name])
            except ValueError, e:
                return []

            self.was_used = True
            self._queryset = (Award.objects
                .filter(user=self.request.user,
                        created__gte=datetime.fromtimestamp(last_check))
                .exclude(hidden=True))

        return self._queryset

    def __iter__(self):
        return self.recent_awards.iterator()

    def __len__(self):
        return len(self.recent_awards)


class RecentAwardsMiddleware(object):
    """Middleware that checks for recent badge awards for the current user"""

    def process_request(self, request):
        if not request.user.is_authenticated():
            # Only authenticated users get awards
            request.recent_awards = None
        elif LAST_AWARD_CHECK_COOKIE_NAME not in request.COOKIES:
            # If no cookie, set one later but avoid a query now.
            request.recent_awards = None
        else:
            request.recent_awards = RecentAwardsList(request)

    def process_response(self, request, response):
        if not request.user.is_authenticated():
            pass
        elif request.recent_awards is None or request.recent_awards.was_used:
            response.set_cookie(LAST_AWARD_CHECK_COOKIE_NAME, time.time())
        return response
