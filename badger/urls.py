from django.conf.urls.defaults import *

from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template


urlpatterns = patterns('badger.views',
    url(r'^$', 'index', name='badger.index'),
    url(r'^detail/(?P<slug>[^/]+)/?$', 'detail',
        name='badger.detail'),
    #url(r'^detail/(?P<slug>[^/]+)/json?$', 'detail',
    #    name='badger.detail_json'),
    url(r'^detail/(?P<slug>[^/]+)/awards/(?P<id>[^/]+)/?$', 'award_detail',
        name='badger.award_detail'),
    url(r'^detail/(?P<slug>[^/]+)/awards/?$', 'awards_by_badge',
        name='badger.awards_by_badge'),
    url(r'^users/(?P<username>[^/]+)/awards/?$', 'awards_by_user',
        name='badger_awards_by_user'),
)
