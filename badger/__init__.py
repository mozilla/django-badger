from django.conf import settings
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

from badger.models import Badge, Award, Progress


def autodiscover():
    """
    Auto-discover INSTALLED_APPS badges.py modules and fail silently when
    not present.
    """
    from django.utils.importlib import import_module
    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            badges_mod = import_module('%s.badges' % app)
            if hasattr(badges_mod, 'register_signals'):
                badges_mod.register_signals()
        except ImportError:
            if module_has_submodule(mod, 'badges'):
                raise
