from django.conf.urls.defaults import *

from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template


urlpatterns = patterns('badger.views',
    url(r'^$', 'index', name='badger_index'),
    url(r'^detail/(?P<slug>[^/]+)/?$', 'detail',
        name='badger_badge_detail'),
    url(r'^detail/(?P<slug>[^/]+)/awards/?$', 'awards_by_badge',
        name='badger_awards_by_badge'),
    url(r'^users/(?P<username>[^/]+)/awards/?$', 'awards_by_user',
        name='badger_awards_by_user'),
)
