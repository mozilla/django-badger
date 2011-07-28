import logging

from django.conf import settings
from django.db.models import signals

from .models import GuestbookEntry

from badger import utils
from badger.models import Badge, Nomination, Award


def update_badges(overwrite=False):
    badge_data = [
        dict(title="Test #2",
             description="Second badge"),
        dict(title="100 Words",
             description="You've written 100 words"),
        dict(title="Master Badger",
             description="You've collected all badges"),
    ]
    return utils.update_badges(badge_data, overwrite)


def award_on_first_post(sender, **kwargs):
    b = Badge.objects.get(slug='first-post')
    if kwargs['created']:
        o = kwargs['instance']
        b.award_to(None, o.creator)


def register_signals():
    signals.post_save.connect(award_on_first_post, sender=GuestbookEntry)
