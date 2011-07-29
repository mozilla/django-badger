import logging

from django.conf import settings
from django.db.models.signals import post_save

from .models import GuestbookEntry

import badger
from badger import utils
from badger.models import Badge, Nomination, Award, Progress


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


def on_guestbook_post(sender, **kwargs):
    o = kwargs['instance']

    if kwargs['created']:
        badger.award('first-post', o.creator)

    p = badger.progress('100-words', o.creator).increment_by(o.word_count)
    if p.counter >= 100:
        badger.award('100-words', o.creator)


def register_signals():
    post_save.connect(on_guestbook_post, sender=GuestbookEntry)
