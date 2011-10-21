from django.conf.urls.defaults import *

from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template

from .feeds import BadgesRecentFeed, BadgesByUserFeed


urlpatterns = patterns('badger_multiplayer.views',
    url(r'^/create$', 'create', 
        name='badger_multiplayer.create_badge'),
    url(r'^badge/(?P<slug>[^/]+)/nominate$', 'nominate_for', 
        name='badger_multiplayer.nominate_for'),
    url(r'^badge/(?P<slug>[^/]+)/edit$', 'edit', 
        name='badger_multiplayer.badge_edit'),
    url(r'^badge/(?P<slug>[^/]+)/nominations/(?P<id>[^/]+)/?$', 'nomination_detail',
        name='badger.nomination_detail'),
    url(r'^users/(?P<username>[^/]+)/badges/?$', 'badges_by_user',
        name='badger_multiplayer.badges_by_user'),

    url(r'^feeds/(?P<format>[^/]+)/badges/?$', BadgesRecentFeed(), 
        name="badger_multiplayer.feeds.badges_recent"),
    url(r'^feeds/(?P<format>[^/]+)/users/(?P<username>[^/]+)/badges/?$',
        BadgesByUserFeed(), 
        name="badger_multiplayer.feeds.badges_by_user"),
)
