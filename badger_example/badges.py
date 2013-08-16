from django.conf import settings
from django.db.models import Sum
from django.db.models.signals import post_save

from .models import GuestbookEntry

import badger
import badger.utils
from badger.utils import get_badge, award_badge, get_progress
from badger.models import Badge, Award, Progress
from badger.signals import badge_was_awarded


badges = [

    dict(slug="test-2",
         title="Test #2",
         description="Second badge"),

    dict(slug="awesomeness",
         title="Awesomeness (you have it)",
         description="Badge with a slug not derived from title."),

    dict(slug="250-words",
         title="250 Words",
         description="You've posted 250 words to my guestbook!"),

    dict(slug="250-words-by-percent",
         title="100% of 250 Words",
         description="You've posted 100% of 250 words to my guestbook!"),

]


def update_badges(overwrite=False):
    badges = [
        dict(slug="master-badger",
             title="Master Badger",
             description="You've collected all badges",
             prerequisites=('test-1', 'test-2', 'awesomeness',
                            'button-clicker')),
    ]

    return badger.utils.update_badges(badges, overwrite)


def on_guestbook_post(sender, **kwargs):
    o = kwargs['instance']
    created = kwargs['created']

    if created:
        award_badge('first-post', o.creator)

    # Increment progress counter and track the completion condition ourselves.
    b = get_badge('250-words')
    p = b.progress_for(o.creator).increment_by(o.word_count)
    if p.counter >= 250:
        b.award_to(o.creator)

    # Update percentage from total word count, and Progress will award on 100%
    total_word_count = (GuestbookEntry.objects.filter(creator=o.creator)
                        .aggregate(s=Sum('word_count'))['s'])
    (get_progress("250-words-by-percent", o.creator)
           .update_percent(total_word_count, 250))


def on_badge_award(sender, signal, award, **kwargs):
    pass


def register_signals():
    post_save.connect(on_guestbook_post, sender=GuestbookEntry)
    badge_was_awarded.connect(on_badge_award, sender=Badge)
