from django.contrib import admin

from django import forms
from django.db import models

try:
    from funfactory.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

import badger.models
from .models import (Badge, Award, Nomination)
from badger.admin import (BadgeAdmin, AwardAdmin, show_unicode,
                          build_related_link)


def award_link(self):
    url = reverse('admin:badger_award_change', args=[self.award.id])
    return '<a href="%s">%s</a>' % (url, self.award)

award_link.allow_tags = True
award_link.short_description = 'award'


class NominationAdmin(admin.ModelAdmin):
    list_display = ('id', show_unicode, award_link, 'accepted', 'nominee',
                    'approver', 'creator', 'created', 'modified',)
    list_filter = ('accepted',)
    search_fields = ('badge__title', 'badge__slug', 'badge__description',)


for x in ((Badge, BadgeAdmin),
          (Award, AwardAdmin),
          (Nomination, NominationAdmin),):
    admin.site.register(*x)
