from django.contrib import admin

from django import forms
from django.db import models

from .models import (Badge, Nomination)


class NominationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Nomination, NominationAdmin)
