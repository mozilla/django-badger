from django.conf import settings
from django.db.models import signals

import badger
from badger.models import Badge, Nomination, Award


def update_badges(badge_data, overwrite=False):
    """Update badges from array of dicts, with option to overwrite existing"""
    badges = []
    for data in badge_data:

        # If there are prerequisites, ensure they're real badges and remove
        # from the set of data fields.
        if 'prerequisites' not in data:
            prerequisites = None
        else:
            prerequisites = [badger.badge(id)
                for id in data.get('prerequisites', [])]
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

        badges.append(badge)

    return badges
