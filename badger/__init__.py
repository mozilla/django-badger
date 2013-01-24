import logging

from django.conf import settings as django_settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

from badger.models import Badge, Award, Progress


# Default settings follow, overridden with BADGER_ prefix in settings.py       
TEMPLATE_BASE = 'badger'

# Skip baking for now (Issue #139)
BAKE_AWARD_IMAGES = False


class BadgerSettings(object):
    """Dirty settings interface that allows defaults from here to be overidden
    by app settings"""
    def __getattr__(self, name):
        override_name = 'BADGER_%s' % name
        if hasattr(django_settings, override_name):
            return getattr(django_settings, override_name)
        else:
            return globals()[name]


settings = BadgerSettings()


def autodiscover():
    """
    Auto-discover INSTALLED_APPS badges.py modules and fail silently when
    not present.
    """
    from django.utils.importlib import import_module
    for app in django_settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            badges_mod = import_module('%s.badges' % app)
            if hasattr(badges_mod, 'register_signals'):
                badges_mod.register_signals()
        except ImportError:
            if module_has_submodule(mod, 'badges'):
                raise
