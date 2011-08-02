from django.conf import settings
from django.db.models import signals

import badger
from badger.models import Badge, Award, Progress


def update_badges(badge_data, overwrite=False):
    """Update badges from array of dicts, with option to overwrite existing"""
    badges = []
    for data in badge_data:
        badges.append(update_badge(data))
    return badges


def update_badge(data, overwrite=False):
    # If there are prerequisites, ensure they're real badges and remove
    # from the set of data fields.
    if 'prerequisites' not in data:
        prerequisites = None
    else:
        prerequisites = [get_badge(n)
            for n in data.get('prerequisites', [])]
        del data['prerequisites']

    badge, created = Badge.objects.get_or_create(title=data['title'],
                                                 defaults=data)

    # If overwriting, and not just created, then save with current fields.
    if overwrite and not created:
        badge.save(**data)

    # Set prerequisites if overwriting, or badge is newly created.
    if (overwrite or created) and prerequisites:
        badge.prerequisites.clear()
        badge.prerequisites.add(*prerequisites)

    return badge


def get_badge(slug_or_badge):
    """Find a badge by slug or by instance"""
    if isinstance(slug_or_badge, Badge):
        b = slug_or_badge
    else:
        b = Badge.objects.get(slug=slug_or_badge)
    return b


def award_badge(slug_or_badge, awardee, awarder=None):
    """Award a badge to an awardee, with optional awarder"""
    b = get_badge(slug_or_badge)
    return b.award_to(awardee, awarder)


def get_progress(slug_or_badge, user):
    """Get a progress record for a badge and awardee"""
    b = get_badge(slug_or_badge)
    return b.progress_for(user)
