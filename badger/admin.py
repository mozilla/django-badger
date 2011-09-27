from django.conf import settings
from django.contrib import admin

from django import forms
from django.db import models

from .models import (Badge, Award, Progress)


UPLOADS_URL = getattr(settings, 'BADGER_UPLOADS_URL',
    '%suploads/' % getattr(settings, 'MEDIA_URL', '/media/'))


def show_unicode(obj):
    return unicode(obj)
show_unicode.short_description = "Display"


def show_image(obj):
    img_url = "%s%s" % (UPLOADS_URL, obj.image)
    return ('<a href="%s" target="_new"><img src="%s" width="64" height="64" /></a>' % 
        (img_url, img_url))
show_image.allow_tags = True
show_image.short_description = "Image"


class BadgerAdmin(admin.ModelAdmin):

    list_display = ("title", "slug", "unique", "creator", show_image, "created", )

    filter_horizontal = ('prerequisites', )

    formfield_overrides = {
        models.ManyToManyField: {
            "widget": forms.widgets.SelectMultiple(attrs={"size": 25})
        }
    }


class AwardAdmin(admin.ModelAdmin):

    list_display = (show_unicode, 'badge', 'user', 'creator', show_image, 'created', )

    fields = ('badge', 'user', 'creator', )


class ProgressAdmin(admin.ModelAdmin):
    pass


admin.site.register(Badge, BadgerAdmin)
admin.site.register(Award, AwardAdmin)
admin.site.register(Progress, ProgressAdmin)
