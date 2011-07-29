from django.conf import settings

from badger.models import Badge, Nomination, Award, Progress


def autodiscover():
    """
    Auto-discover INSTALLED_APPS badges.py modules and fail silently when
    not present.
    """
    from django.utils.importlib import import_module
    for app in settings.INSTALLED_APPS:
        try:
            badges_mod = import_module('%s.badges' % app)
        except ImportError:
            continue
        badges_mod.register_signals()


def badge(slug_or_badge):
    """Find a badge by slug or by instance"""
    if isinstance(slug_or_badge, Badge):
        b = slug_or_badge
    else:
        b = Badge.objects.get(slug=slug_or_badge)
    return b


def award(slug_or_badge, awardee, awarder=None):
    """Award a badge to an awardee, with optional awarder"""
    b = badge(slug_or_badge)
    return b.award_to(awardee, awarder)


def progress(slug_or_badge, user):
    """Get a progress record for a badge and awardee"""
    b = badge(slug_or_badge)
    return b.progress_for(user)
