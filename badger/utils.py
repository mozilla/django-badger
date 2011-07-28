from django.conf import settings
from django.db.models import signals

from badger.models import Badge, Nomination, Award


def update_badges(badge_data, overwrite=False):
    """Update badges from array of dicts, with option to overwrite existing"""
    badges = []
    for data in badge_data:
        badge, created = Badge.objects.get_or_create(title=data['title'], defaults=data)
        if overwrite and not created:
            badge.save(**data)
        badges.append(badge)
    return badges
