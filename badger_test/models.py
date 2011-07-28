from django.db import models
from django.contrib.auth.models import User

from django.template.defaultfilters import slugify


class GuestbookEntry(models.Model):
    """Representation of a badge"""
    message = models.TextField(blank=True)
    creator = models.ForeignKey(User, blank=False)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    @property
    def word_count(self):
        return len(self.message.split(' '))
