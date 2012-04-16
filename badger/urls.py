from django.conf.urls.defaults import *

from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template

from .feeds import AwardsRecentFeed, AwardsByUserFeed, AwardsByBadgeFeed


urlpatterns = patterns('badger.views',
    url(r'^$', 'badges_list', name='badger.badges_list'),
    url(r'^tag/(?P<tag_name>[^/]+)/?$', 'badges_list',
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
    url(r'^badge/(?P<slug>[^/]+)/claims/?$', 'manage_claims',
        name='badger.manage_claims'),
    url(r'^badge/(?P<slug>[^/]+)/claims/(?P<claim_group>[^/]+)/?$', 'claims_list',
        name='badger.claims_list'),
    url(r'^claim/(?P<claim_code>[^/]+)/?$', 'claim_deferred_award',
        name='badger.claim_deferred_award'),
    url(r'^claim/?$', 'claim_deferred_award',
        name='badger.claim_deferred_award_form'),
    url(r'^badge/(?P<slug>[^/]+)/award', 'award_badge',
        name='badger.award_badge'),
    url(r'^badge/(?P<slug>[^\.]+)\.json$', 'detail',
        kwargs=dict(format="json"),
        name='badger.detail_json'),
    url(r'^badge/(?P<slug>[^/]+)/?$', 'detail',
        name='badger.detail'),
    url(r'^badge/(?P<slug>[^/]+)/awards/?$', 'awards_by_badge',
        name='badger.awards_by_badge'),
    url(r'^users/(?P<username>[^/]+)/awards/?$', 'awards_by_user',
        name='badger.awards_by_user'),

    url(r'^feeds/(?P<format>[^/]+)/awards/?$',
        AwardsRecentFeed(), name="badger.feeds.awards_recent"),
    url(r'^feeds/(?P<format>[^/]+)/badge/(?P<slug>[^/]+)/awards/?$',
        AwardsByBadgeFeed(), name="badger.feeds.awards_by_badge"),
    url(r'^feeds/(?P<format>[^/]+)/users/(?P<username>[^/]+)/awards/?$',
        AwardsByUserFeed(), name="badger.feeds.awards_by_user"),
)
