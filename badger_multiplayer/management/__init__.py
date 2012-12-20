from os.path import dirname, basename

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_apps, get_models, signals
from django.utils.importlib import import_module
from django.utils.module_loading import module_has_submodule

import badger


if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
    from django.utils.translation import ugettext_noop as _

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notices = (
            ("nomination_submitted", _("Nomination submitted"),
                _("someone has submitted a nomination for one of your badges")),
            ("nomination_approved", _("Nomination approved"),
                _("a nomination you submitted for an award has been approved")),
            #("nomination_rejected", _("Nomination rejected"),
            #    _("a nomination you submitted for an award has been rejected")),
            ("nomination_received", _("Nomination received"),
                _("a nomination to award you a badge was approved")),
            ("nomination_accepted", _("Nomination accepted"),
                _("a nomination you submitted for an award has been accepted")),
            #("nomination_declined", _("Nomination declined"),
            #    _("a nomination you submitted for an award has been declined")),
        )
        for notice in notices:
            notification.create_notice_type(*notice)

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
