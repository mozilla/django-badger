from django.conf import settings
from django.contrib import admin

from django import forms
from django.db import models

try:
    from funfactory.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

from .models import (Badge, Award, Progress, DeferredAward)


UPLOADS_URL = getattr(settings, 'BADGER_UPLOADS_URL',
    '%suploads/' % getattr(settings, 'MEDIA_URL', '/media/'))


def show_unicode(obj):
    return unicode(obj)
show_unicode.short_description = "Display"


def show_image(obj):
    img_url = "%s%s" % (UPLOADS_URL, obj.image)
    return ('<a href="%s" target="_new"><img src="%s" width="48" height="48" /></a>' % 
        (img_url, img_url))

show_image.allow_tags = True
show_image.short_description = "Image"


def build_related_link(self, model_name, name_single, name_plural, qs):
    link = '%s?%s' % (
        reverse('admin:badger_%s_changelist' % model_name, args=[]),
        'badge__exact=%s' % (self.id)
    )
    new_link = '%s?%s' % (
        reverse('admin:badger_%s_add' % model_name, args=[]),
        'badge=%s' % (self.id)
    )
    count = qs.count()
    what = (count == 1) and name_single or name_plural
    return ('<a href="%s">%s %s</a> (<a href="%s">new</a>)' %
            (link, count, what, new_link))


def related_deferredawards_link(self):
    return build_related_link(self, 'deferredaward', 'deferred', 'deferred',
                              self.deferredaward_set)

related_deferredawards_link.allow_tags = True
related_deferredawards_link.short_description = "Deferred Awards"


def related_awards_link(self):
    return build_related_link(self, 'award', 'award', 'awards',
                              self.award_set)

related_awards_link.allow_tags = True
related_awards_link.short_description = "Awards"


class BadgeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", show_image, "slug", "unique", "creator",
                    related_awards_link, related_deferredawards_link, "created",)
    list_display_links = ('id', 'title',)
    search_fields = ("title", "slug", "image", "description",)
    filter_horizontal = ('prerequisites', )
    prepopulated_fields = {"slug": ("title",)}
    formfield_overrides = {
        models.ManyToManyField: {
            "widget": forms.widgets.SelectMultiple(attrs={"size": 25})
        }
    }


def badge_link(self):
    url = reverse('admin:badger_badge_change', args=[self.badge.id])
    return '<a href="%s">%s</a>' % (url, self.badge)

badge_link.allow_tags = True
badge_link.short_description = 'Badge'


class AwardAdmin(admin.ModelAdmin):
    list_display = (show_unicode, badge_link, show_image, 'user', 'creator',
                    'created', )
    fields = ('badge', 'user', 'creator', )
    search_fields = ("badge__title", "badge__slug", "badge__description",)


class ProgressAdmin(admin.ModelAdmin):
    pass


def claim_code_link(self):
    return '<a href="%s">%s</a>' % (self.get_claim_url(), self.claim_code)

claim_code_link.allow_tags = True
claim_code_link.short_description = "Claim Code"


class DeferredAwardAdmin(admin.ModelAdmin):
    list_display = ('id', claim_code_link, 'claim_group', badge_link, 'email',
                    'reusable', 'creator', 'created', 'modified',)
    list_display_links = ('id',)
    list_filter = ('reusable', )    
    fields = ('badge', 'claim_code', 'email', 'reusable', 'description',)
    readonly_fields = ('created', 'modified')
    search_fields = ("badge__title", "badge__slug", "badge__description",)


for x in ((Badge, BadgeAdmin),
          (Award, AwardAdmin),
          (Progress, ProgressAdmin),
          (DeferredAward, DeferredAwardAdmin),):
    admin.site.register(*x)
