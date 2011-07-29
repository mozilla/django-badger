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


def find_badge(slug_or_badge):
    if isinstance(slug_or_badge, Badge):
        b = slug_or_badge
    else:
        b = Badge.objects.get(slug=slug_or_badge)
    return b


def award(slug_or_badge, awardee, awarder=None):
    b = find_badge(slug_or_badge)
    return b.award_to(awardee, awarder)


def progress(slug_or_badge, awardee):
    b = find_badge(slug_or_badge)
    p, created = Progress.objects.get_or_create(user=awardee, badge=b) 
    return p
