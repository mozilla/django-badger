from django.conf import settings


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
