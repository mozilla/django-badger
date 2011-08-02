from django.contrib import admin

from django import forms
from django.db import models

from .models import (Badge, Award, Progress)


class BadgerAdmin(admin.ModelAdmin):
    list_display = ("title", )

    filter_horizontal = ('prerequisites', )

    formfield_overrides = {
        models.ManyToManyField: {
            "widget": forms.widgets.SelectMultiple(attrs={"size": 25})
        }
    }


admin.site.register(Badge, BadgerAdmin)


class AwardAdmin(admin.ModelAdmin):
    pass


admin.site.register(Award, AwardAdmin)


class ProgressAdmin(admin.ModelAdmin):
    pass


admin.site.register(Progress, ProgressAdmin)
