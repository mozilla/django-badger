import hashlib
import urllib

from django.conf import settings

from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

try:
    from tower import ugettext_lazy as _
except ImportError, e:
    from django.utils.translation import ugettext_lazy as _

import jingo
import jinja2
from jinja2 import evalcontextfilter, Markup, escape
from jingo import register, env

from badger.models import (Progress,
        BadgeAwardNotAllowedException)

from .models import Badge, Award, Nomination

@register.function
def nominations_pending_approval(user):
    return Nomination.objects.filter(badge__creator=user,
                                     approver__isnull=True)

@register.function
def nominations_pending_acceptance(user):
    return Nomination.objects.filter(nominee=user,
                                     approver__isnull=False,
                                     accepted=False)
