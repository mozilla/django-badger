from django.conf.urls.defaults import *

from django.conf import settings
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('badger.views',
    url(r'^$', 'home', name='badger_home'),
    url(r'^create$', 'create', name='badger_create_badge'),
    url(r'^badges/(?P<slug>[^/]+)/?$', 'detail', name='badger_badge_detail'),
)
