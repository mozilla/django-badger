import logging

from django.conf import settings
from django.db.models import signals

from .models import GuestbookEntry

from badger.models import Badge, Nomination, Award


def update_badges():
    pass


def award_on_first_post(sender, **kwargs):
    b = Badge.objects.get(slug='first-post')
    if kwargs['created']:
        o = kwargs['instance']
        b.award_to(None, o.creator)


def register_signals():
    signals.post_save.connect(award_on_first_post, sender=GuestbookEntry)
