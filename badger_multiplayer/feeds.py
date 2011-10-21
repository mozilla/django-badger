"""Feeds for badge"""
import datetime
import hashlib
import urllib

import jingo

from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.utils.feedgenerator import (SyndicationFeed, Rss201rev2Feed,
                                        Atom1Feed, get_tag_uri)
import django.utils.simplejson as json
from django.shortcuts import get_object_or_404

from django.contrib.auth.models import User
from django.conf import settings

try:
    from tower import ugettext_lazy as _
except ImportError, e:
    from django.utils.translation import ugettext_lazy as _

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

from badger import validate_jsonp
from badger.models import (Badge, Award, Progress,
        BadgeAwardNotAllowedException)
from badger.feeds import (MAX_FEED_ITEMS, BaseJSONFeedGenerator, BaseFeed,
                          AwardsFeed)


class BadgesJSONFeedGenerator(BaseJSONFeedGenerator):
    pass


class BadgesFeed(BaseFeed):
    """Base class for all feeds listing badges"""
    title = _('Recently created badges')

    json_feed_generator = BadgesJSONFeedGenerator

    def item_title(self, obj):
        return obj.title

    def item_link(self, obj):
        return self.request.build_absolute_uri(
            reverse('badger.views.detail',
                    args=(obj.slug, )))


class BadgesRecentFeed(BadgesFeed):

    def items(self):
        return (Badge.objects
                .order_by('-created')
                .all()[:MAX_FEED_ITEMS])


class BadgesByUserFeed(BadgesFeed):
    """Feed of badges recently created by a user"""

    def get_object(self, request, format, username):
        super(BadgesByUserFeed, self).get_object(request, format)
        user = get_object_or_404(User, username=username)
        self.title = _("Badges recently created by %s") % user.username
        self.link = request.build_absolute_uri(
            reverse('badger_multiplayer.views.badges_by_user', args=(user.username,)))
        return user

    def items(self, user):
        return (Badge.objects
                .filter(creator=user)
                .order_by('-created')
                .all()[:MAX_FEED_ITEMS])
