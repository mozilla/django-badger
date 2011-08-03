from django.contrib import admin

from django import forms
from django.db import models

import badger.models
from .models import (Badge, Nomination)


class BadgerAdmin(admin.ModelAdmin):
    list_display = ("title", )

    filter_horizontal = ('prerequisites', )

    formfield_overrides = {
        models.ManyToManyField: {
            "widget": forms.widgets.SelectMultiple(attrs={"size": 25})
        }
    }


admin.site.register(Badge, BadgerAdmin)


class NominationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Nomination, NominationAdmin)
