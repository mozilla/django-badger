import logging
import time
from datetime import datetime
from django.conf import settings

from .models import (Badge, Award)


LAST_CHECK_COOKIE_NAME = getattr(settings,
    'BADGER_LAST_CHECK_COOKIE_NAME', 'badgerLastAwardCheck')


class RecentBadgeAwardsList(object):
    """Very lazy accessor for recent awards."""

    def __init__(self, request):
        self.request = request
        self.was_used = False
        self._queryset = None

        # Try to fetch and parse the timestamp of the last award check, fall
        # back to None
        try:
            self.last_check = datetime.fromtimestamp(float(
                self.request.COOKIES[LAST_CHECK_COOKIE_NAME]))
        except (KeyError, ValueError):
            self.last_check = None

    def process_response(self, response):
        if (self.request.user.is_authenticated() and
                (not self.last_check or self.was_used)):
            response.set_cookie(LAST_CHECK_COOKIE_NAME, time.time())
        return response

    def get_queryset(self, last_check=None):
        if not last_check:
            last_check = self.last_check

        if not (last_check and self.request.user.is_authenticated()):
            # No queryset for anonymous users or missing last check timestamp
            return None

        if not self._queryset:
            self.was_used = True
            self._queryset = (Award.objects
                .filter(user=self.request.user,
                        created__gt=last_check)
                .exclude(hidden=True))

        return self._queryset

    def __iter__(self):
        qs = self.get_queryset()
        if qs is None:
            return []
        return qs.iterator()

    def __len__(self):
        qs = self.get_queryset()
        if qs is None:
            return 0
        return len(qs)


class RecentBadgeAwardsMiddleware(object):
    """Middleware that adds ``recent_badge_awards`` to request

    This property is lazy-loading, so if you don't use it, then it
    shouldn't have much effect on runtime.

    To use, add this to your ``MIDDLEWARE_CLASSES`` in ``settings.py``::

        MIDDLEWARE_CLASSES = (
            ...
            'badger.middleware.RecentBadgeAwardsMiddleware',
            ...
        )


    Then in your view code::

        def awesome_view(request):
            for award in request.recent_badge_awards:
                do_something_awesome(award)

    """

    def process_request(self, request):
        request.recent_badge_awards = RecentBadgeAwardsList(request)
        return None

    def process_response(self, request, response):
        if not hasattr(request, 'recent_badge_awards'):
            return response
        return request.recent_badge_awards.process_response(response)
