import logging

from django.conf import settings
from django.db.models.signals import post_save

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
        b.award_to(o.creator)


def track_guestbook_word_count(sender, **kwargs):
    b = Badge.objects.get(slug='100-words')
    post = kwargs['instance']


def register_signals():
    post_save.connect(track_guestbook_word_count, sender=GuestbookEntry)
    post_save.connect(award_on_first_post, sender=GuestbookEntry)
