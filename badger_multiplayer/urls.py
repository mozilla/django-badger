from django.conf.urls.defaults import *

from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template

from .feeds import BadgesRecentFeed


urlpatterns = patterns('badger_multiplayer.views',
    url(r'^;create$', 'create', 
        name='badger_multiplayer.create_badge'),
    url(r'^detail/(?P<slug>[^/]+);nominate$', 'nominate_for', 
        name='badger_multiplayer.nominate_for'),
    url(r'^detail/(?P<slug>[^/]+);edit$', 'edit', 
        name='badger_multiplayer.badge_edit'),
    url(r'^detail/(?P<slug>[^/]+)/nominations/(?P<id>[^/]+)/?$', 'nomination_detail',
        name='badger.nomination_detail'),

    url(r'^feeds/(?P<format>[^/]+)/badges/?$', BadgesRecentFeed(), 
        name="badger_multiplayer.feeds.badges_recent"),
)
