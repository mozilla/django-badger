import hashlib
import urllib

from django.conf import settings

from django.contrib.auth.models import SiteProfileNotAvailable
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import conditional_escape

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
            urllib.urlencode({'chs':'%sx%s' % (size, size), 'cht':'qr', 'chl':value, 'choe':'UTF-8'}))
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


@register.filter
def urlparams(url_, hash=None, **query):
    """Add a fragment and/or query paramaters to a URL.

    New query params will be appended to exising parameters, except duplicate
    names, which will be replaced.
    """
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    # Use dict(parse_qsl) so we don't get lists of values.
    q = url.query
    query_dict = dict(urlparse.parse_qsl(smart_str(q))) if q else {}
    query_dict.update((k, v) for k, v in query.items())

    query_string = _urlencode([(k, v) for k, v in query_dict.items()
                               if v is not None])
    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return new.geturl()


def _urlencode(items):
    """A Unicode-safe URLencoder."""
    try:
        return urllib.urlencode(items)
    except UnicodeEncodeError:
        return urllib.urlencode([(k, smart_str(v)) for k, v in items])
