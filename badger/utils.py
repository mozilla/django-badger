from django.conf import settings
from django.db.models import signals

import badger
from badger.models import Badge, Award, Progress


def update_badges(badge_data, overwrite=False):
    """Creates or updates list of badges

    :arg badge_data: list of dicts. keys in the dict correspond to the
        Badge model class. Also, you can pass in ``prerequisites``.
    :arg overwrite: whether or not to overwrite the existing badge

    :returns: list of Badge instances---one per dict passed in

    """
    badges = []
    for data in badge_data:
        badges.append(update_badge(data, overwrite=overwrite))
    return badges


def update_badge(data_in, overwrite=False):
    # Clone the data, because we might delete fields
    data = dict(**data_in)

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
        for k, v in data.items():
            setattr(badge, k, v)
        badge.save()

    # Set prerequisites if overwriting, or badge is newly created.
    if (overwrite or created) and prerequisites:
        badge.prerequisites.clear()
        badge.prerequisites.add(*prerequisites)

    return badge


def get_badge(slug_or_badge):
    """Return badge specified by slug or by instance

    :arg slug_or_badge: slug or Badge instance

    :returns: Badge instance

    """
    if isinstance(slug_or_badge, Badge):
        b = slug_or_badge
    else:
        b = Badge.objects.get(slug=slug_or_badge)
    return b


def award_badge(slug_or_badge, awardee, awarder=None):
    """Award a badge to an awardee, with optional awarder

    :arg slug_or_badge: slug or Badge instance to award
    :arg awardee: User this Badge is awarded to
    :arg awarder: User who awarded this Badge

    :returns: Award instance

    :raise BadgeAwardNotAllowedexception: ?

    :raise BadgeAlreadyAwardedException: if the badge is unique and
        has already been awarded to this user

    """
    b = get_badge(slug_or_badge)
    return b.award_to(awardee=awardee, awarder=awarder)


def get_progress(slug_or_badge, user):
    """Get a progress record for a badge and awardee

    :arg slug_or_badge: slug or Badge instance
    :arg user: User to check progress for

    :returns: Progress instance

    """
    b = get_badge(slug_or_badge)
    return b.progress_for(user)
