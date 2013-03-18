from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

import badger
badger.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'badger_example.views.home', name='home'),
    # url(r'^badger_example/', include('badger_example.foo.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^badges/', include('badger.urls')),
)
