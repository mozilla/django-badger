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

from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import (Progress,
        BadgeAwardNotAllowedException)

# TODO: Is there an extensible way to do this, where "add-ons" introduce proxy
# model objects?
try:
    from badger_multiplayer.models import Badge, Award, DeferredAward
except ImportError:
    from badger.models import Badge, Award, DeferredAward

from .forms import (BadgeAwardForm)

BADGE_PAGE_SIZE = 21
MAX_RECENT = 15


def home(request):
    """Badger home page"""
    return render_to_response('badger/home.html', dict(
        badge_list=Badge.objects.order_by('-modified').all()[:MAX_RECENT],
        award_list=Award.objects.order_by('-modified').all()[:MAX_RECENT],
    ), context_instance=RequestContext(request))


def badges_list(request):
    """Badges list page"""
    query_string = request.GET.get('q', None)
    if query_string is not None:
        sort_order = request.GET.get('sort', 'created')
        queryset = Badge.objects.search(query_string, sort_order)
    else: 
        queryset = Badge.objects.order_by('-modified').all()
    return object_list(request, queryset,
        paginate_by=BADGE_PAGE_SIZE, allow_empty=True,
        extra_context=dict(
            query_string=query_string
        ),
        template_object_name='badge',
        template_name='badger/badges_list.html')


@require_http_methods(['HEAD', 'GET'])
def detail(request, slug, format="html"):
    """Badge detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_detail_by(request.user):
        return HttpResponseForbidden()

    awards = (Award.objects.filter(badge=badge)
                           .order_by('-created'))[:MAX_RECENT]

    if format == 'json':
        data = badge.as_obi_serialization(request)
        resp = HttpResponse(simplejson.dumps(data))
        resp['Content-Type'] = 'application/json'
        return resp
    else:
        return render_to_response('badger/badge_detail.html', dict(
            badge=badge, award_list=awards,
        ), context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
def award_badge(request, slug):
    """Issue an award for a badge"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_award_to(request.user):
        return HttpResponseForbidden()

    if request.method != "POST":
        form = BadgeAwardForm()
    else:
        form = BadgeAwardForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            result = badge.award_to(email=email, awarder=request.user)
            if result:
                if not hasattr(result, 'claim_code'):
                    messages.info(request, _('Award issued to %s') % email)
                    return HttpResponseRedirect(
                            reverse('badger.views.detail', 
                                    args=(badge.slug,)))
                else:
                    messages.info(request, _('Invitation to claim award '
                                             'sent to %s') % email)
                    return HttpResponseRedirect(
                            reverse('badger.views.detail', 
                                    args=(badge.slug,)))

    return render_to_response('badger/badge_award.html', dict(
        form=form, badge=badge,
    ), context_instance=RequestContext(request))


@require_GET
def awards_list(request, slug=None):
    queryset = Award.objects
    if not slug:
        badge = None
    else:
        badge = get_object_or_404(Badge, slug=slug)
        queryset = queryset.filter(badge=badge)
    queryset = queryset.order_by('-modified').all()

    return object_list(request, queryset,
        paginate_by=BADGE_PAGE_SIZE, allow_empty=True,
        extra_context=dict(
            badge=badge
        ),
        template_object_name='award',
        template_name='badger/awards_list.html')


@require_http_methods(['HEAD', 'GET'])
def award_detail(request, slug, id, format="html"):
    """Award detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    award = get_object_or_404(Award, badge=badge, pk=id)
    if not award.allows_detail_by(request.user):
        return HttpResponseForbidden()

    if format == 'json':
        data = simplejson.dumps(award.as_obi_assertion(request))
        resp = HttpResponse(data)
        resp['Content-Type'] = 'application/json'
        return resp
    else:
        return render_to_response('badger/award_detail.html', dict(
            badge=badge, award=award,
        ), context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
def claim_deferred_award(request, claim_code=None):
    """Deferred award detail view"""
    if not claim_code:
        claim_code = request.GET.get('code', '').strip()
    deferred_award = get_object_or_404(DeferredAward, claim_code=claim_code)
    if not deferred_award.allows_claim_by(request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
        award = deferred_award.claim(request.user)
        if award:
            return HttpResponseRedirect(reverse('badger.views.award_detail',
                                                args=(award.badge.slug,
                                                      award.id,)))

    return render_to_response('badger/claim_deferred_award.html', dict(
        badge=deferred_award.badge, deferred_award=deferred_award,
    ), context_instance=RequestContext(request))


@require_GET
def awards_by_user(request, username):
    """Badge awards by user"""
    user = get_object_or_404(User, username=username)
    awards = Award.objects.filter(user=user)
    return render_to_response('badger/awards_by_user.html', dict(
        user=user, award_list=awards,
    ), context_instance=RequestContext(request))


@require_GET
def awards_by_badge(request, slug):
    """Badge awards by badge"""
    badge = get_object_or_404(Badge, slug=slug)
    awards = Award.objects.filter(badge=badge)
    return render_to_response('badger/awards_by_badge.html', dict(
        badge=badge, awards=awards,
    ), context_instance=RequestContext(request))
