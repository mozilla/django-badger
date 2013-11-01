from os.path import dirname, basename

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_apps, get_models, signals
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

import badger
import badger.utils


if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
    from django.utils.translation import ugettext_noop as _

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notices = (
            ("badge_edited", _(u"Badge edited"),
                _(u"one of your badges has been edited")),
            ("badge_awarded", _(u"Badge awarded"),
                _(u"one of your badges has been awarded to someone")),
            ("award_received", _(u"Award received"),
                _(u"you have been awarded a badge")),
            #("award_accepted", _(u"Badge award accepted"),
            #    _(u"someone has accepted an award for one of your badges")),
            #("award_declined", _(u"Badge award declined"),
            #    _(u"someone has declined an award for one of your badges")),
            # TODO: Notification on progress?
            ("nomination_submitted", _(u"Nomination submitted"),
                _(u"someone has submitted a nomination for one of your badges")),
            ("nomination_approved", _(u"Nomination approved"),
                _(u"a nomination you submitted for an award has been approved")),
            ("nomination_rejected", _(u"Nomination rejected"),
                _(u"a nomination you submitted for an award has been rejected")),
            ("nomination_received", _(u"Nomination received"),
                _(u"a nomination to award you a badge was approved")),
            ("nomination_accepted", _(u"Nomination accepted"),
                _(u"a nomination you submitted for an award has been accepted")),
        )
        for notice in notices:
            notification.create_notice_type(*notice)

    signals.post_syncdb.connect(create_notice_types, sender=notification)


def update_badges(overwrite=False):
    from django.utils.importlib import import_module

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            badges_mod = import_module('%s.badges' % app)
            fixture_label = '%s_badges' % app.replace('.','_')
            call_command('loaddata', fixture_label, verbosity=1)
            if hasattr(badges_mod, 'badges'):
                badger.utils.update_badges(badges_mod.badges, overwrite)
            if hasattr(badges_mod, 'update_badges'):
                badges_mod.update_badges(overwrite)
        except ImportError:
            if module_has_submodule(mod, 'badges'):
                raise


signals.post_syncdb.connect(lambda *args, **kwargs: update_badges(),
                            sender=badger.models)
