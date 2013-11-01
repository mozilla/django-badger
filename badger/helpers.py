import hashlib
import urllib
import urlparse

from django.conf import settings

from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import conditional_escape

try:
    from commons.urlresolvers import reverse
except ImportError:
    from django.core.urlresolvers import reverse

import jingo
import jinja2
from jinja2 import evalcontextfilter, Markup, escape
from jingo import register, env

from .models import (Badge, Award, Nomination, Progress,
                     BadgeAwardNotAllowedException)


@register.function
def user_avatar(user, secure=False, size=256, rating='pg', default=''):
    try:
        profile = user.get_profile()
        if profile.avatar:
            return profile.avatar.url
    except AttributeError:
        pass
    except SiteProfileNotAvailable:
        pass
    except ObjectDoesNotExist:
        pass

    base_url = (secure and 'https://secure.gravatar.com' or
        'http://www.gravatar.com')
    m = hashlib.md5(user.email)
    return '%(base_url)s/avatar/%(hash)s?%(params)s' % dict(
        base_url=base_url, hash=m.hexdigest(),
        params=urllib.urlencode(dict(
            s=size, d=default, r=rating
        ))
    )


@register.function
def user_awards(user):
    return Award.objects.filter(user=user)


@register.function
def user_badges(user):
    return Badge.objects.filter(creator=user)


@register.function
def badger_allows_add_by(user):
    return Badge.objects.allows_add_by(user)


@register.function
def qr_code_image(value, alt=None, size=150):
    # TODO: Bake our own QR codes, someday soon!
    url = conditional_escape("http://chart.apis.google.com/chart?%s" % \
            urllib.urlencode({'chs': '%sx%s' % (size, size), 'cht': 'qr', 'chl': value, 'choe': 'UTF-8'}))
    alt = conditional_escape(alt or value)

    return Markup(u"""<img class="qrcode" src="%s" width="%s" height="%s" alt="%s" />""" %
                  (url, size, size, alt))


@register.function
def nominations_pending_approval(user):
    return Nomination.objects.filter(badge__creator=user,
                                     approver__isnull=True)


@register.function
def nominations_pending_acceptance(user):
    return Nomination.objects.filter(nominee=user,
                                     approver__isnull=False,
                                     accepted=False)
