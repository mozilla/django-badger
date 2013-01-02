from django.db import models
from django.contrib.auth.models import User

from django.template.defaultfilters import slugify


class GuestbookEntry(models.Model):
    """Representation of a guestbook entry"""
    message = models.TextField(blank=True)
    creator = models.ForeignKey(User, blank=False)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)
    word_count = models.IntegerField(default=0, blank=True)

    def save(self, *args, **kwargs):
        self.word_count = len(self.message.split(' '))
        super(GuestbookEntry, self).save(*args, **kwargs)
