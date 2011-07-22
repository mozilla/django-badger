from django.contrib import admin

from .models import (Badge, Award, Nomination)


class BadgerAdmin(admin.ModelAdmin):
    list_display = ("title",)


admin.site.register(Badge, BadgerAdmin)


class AwardAdmin(admin.ModelAdmin):
    pass


admin.site.register(Award, AwardAdmin)


class NominationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Nomination, NominationAdmin)
