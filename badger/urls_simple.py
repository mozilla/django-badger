"""
This is a simplified URLs list that omits any of the multiplayer features,
assuming that all badges will be managed from the admin interface, and most
badges will be awarded in badges.py
"""
from django.conf.urls import patterns, include, url

from django.conf import settings

from .feeds import (AwardsRecentFeed, AwardsByUserFeed, AwardsByBadgeFeed,
                    BadgesRecentFeed, BadgesByUserFeed)
from . import views


urlpatterns = patterns('badger.views',
    url(r'^$', 'badges_list', name='badger.badges_list'),
    url(r'^tag/(?P<tag_name>.+)/?$', 'badges_list',
        name='badger.badges_list'),
    url(r'^awards/?', 'awards_list',
        name='badger.awards_list'),
    url(r'^badge/(?P<slug>[^/]+)/awards/?$', 'awards_list',
        name='badger.awards_list_for_badge'),
    url(r'^badge/(?P<slug>[^/]+)/awards/(?P<id>[^\.]+)\.json$', 'award_detail',
        kwargs=dict(format="json"),
        name='badger.award_detail_json'),
    url(r'^badge/(?P<slug>[^/]+)/awards/(?P<id>[^/]+)/?$', 'award_detail',
        name='badger.award_detail'),
    url(r'^badge/(?P<slug>[^/]+)/awards/(?P<id>[^/]+)/delete$', 'award_delete',
        name='badger.award_delete'),
    url(r'^badge/(?P<slug>[^\.]+)\.json$', 'detail',
        kwargs=dict(format="json"),
        name='badger.detail_json'),
    url(r'^badge/(?P<slug>[^/]+)/?$', 'detail',
        name='badger.detail'),
    url(r'^badge/(?P<slug>[^/]+)/awards/?$', 'awards_by_badge',
        name='badger.awards_by_badge'),
    url(r'^users/(?P<username>[^/]+)/awards/?$', 'awards_by_user',
        name='badger.awards_by_user'),
    url(r'^feeds/(?P<format>[^/]+)/badges/?$', BadgesRecentFeed(),
        name="badger.feeds.badges_recent"),
    url(r'^feeds/(?P<format>[^/]+)/awards/?$',
        AwardsRecentFeed(), name="badger.feeds.awards_recent"),
    url(r'^feeds/(?P<format>[^/]+)/badge/(?P<slug>[^/]+)/awards/?$',
        AwardsByBadgeFeed(), name="badger.feeds.awards_by_badge"),
    url(r'^feeds/(?P<format>[^/]+)/users/(?P<username>[^/]+)/awards/?$',
        AwardsByUserFeed(), name="badger.feeds.awards_by_user"),
)
