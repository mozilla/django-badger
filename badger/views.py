import jingo
import logging
import random

from django.conf import settings

from django.http import (HttpResponseRedirect, HttpResponse,
        HttpResponseForbidden, HttpResponseNotFound)

from django.utils import simplejson

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

try:
    from tower import ugettext_lazy as _
except ImportError, e:
    from django.utils.translation import ugettext_lazy as _

from django.views.generic.base import View
from django.views.generic.list_detail import object_list
from django.views.decorators.http import (require_GET, require_POST,
                                          require_http_methods)

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import (Badge, Award, Progress,
        BadgeAwardNotAllowedException)


BADGE_PAGE_SIZE = 14
MAX_RECENT_AWARDS = 9


def index(request):
    """Badger index page"""
    queryset = Badge.objects.order_by('-modified').all()
    return object_list(request, queryset,
        paginate_by=BADGE_PAGE_SIZE, allow_empty=True,
        template_object_name='badge',
        template_name='badger/index.html')


@require_GET
def detail(request, slug, format="html"):
    """Badge detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    awards = (Award.objects.filter(badge=badge)
                           .order_by('-created'))[:MAX_RECENT_AWARDS]

    if format == 'json':
        data = badge.as_obi_serialization(request)
        resp = HttpResponse(simplejson.dumps(data))
        resp['Content-Type'] = 'application/json'
        return resp
    else:
        return render_to_response('badger/badge_detail.html', dict(
            badge=badge, awards=awards,
        ), context_instance=RequestContext(request))


@require_GET
def awards_list(request):
    queryset = Award.objects.order_by('-modified').all()
    return object_list(request, queryset,
        paginate_by=BADGE_PAGE_SIZE, allow_empty=True,
        template_object_name='award',
        template_name='badger/awards_list.html')


@require_GET
def award_detail(request, slug, id, format="html"):
    """Award detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    award = get_object_or_404(Award, badge=badge, pk=id)

    if format == 'json':
        data = simplejson.dumps(award.as_obi_assertion(request))
        resp = HttpResponse(data)
        resp['Content-Type'] = 'application/json'
        return resp
    else:
        return render_to_response('badger/award_detail.html', dict(
            badge=badge, award=award,
        ), context_instance=RequestContext(request))


@require_GET
def awards_by_user(request, username):
    """Badge awards by user"""
    user = get_object_or_404(User, username=username)
    awards = Award.objects.filter(user=user)
    return render_to_response('badger/awards_by_user.html', dict(
        user=user, awards=awards,
    ), context_instance=RequestContext(request))


@require_GET
def awards_by_badge(request, slug):
    """Badge awards by badge"""
    badge = get_object_or_404(Badge, slug=slug)
    awards = Award.objects.filter(badge=badge)
    return render_to_response('badger/awards_by_badge.html', dict(
        badge=badge, awards=awards,
    ), context_instance=RequestContext(request))
