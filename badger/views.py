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

from django.dispatch import receiver
from django.dispatch import Signal

try:
    import taggit
    from taggit.models import Tag, TaggedItem
except:
    taggit = None

from .models import (Progress,
        BadgeAwardNotAllowedException)

# TODO: Is there an extensible way to do this, where "add-ons" introduce proxy
# model objects?
try:
    from badger_multiplayer.models import Badge, Award, DeferredAward
except ImportError:
    from badger.models import Badge, Award, DeferredAward

from .forms import (BadgeAwardForm, DeferredAwardGrantForm,
                    DeferredAwardMultipleGrantForm)

BADGE_PAGE_SIZE = 20
MAX_RECENT = 15

detail_needs_sections = Signal(providing_args=['request', 'badge'])


def home(request):
    """Badger home page"""
    badge_list = Badge.objects.order_by('-modified').all()[:MAX_RECENT]
    award_list = Award.objects.order_by('-modified').all()[:MAX_RECENT]
    badge_tags = Badge.objects.top_tags()

    return render_to_response('badger/home.html', dict(
        badge_list=badge_list, award_list=award_list, badge_tags=badge_tags
    ), context_instance=RequestContext(request))


def badges_list(request, tag_name=None):
    """Badges list page"""
    award_list = None
    query_string = request.GET.get('q', None)
    if query_string is not None:
        sort_order = request.GET.get('sort', 'created')
        queryset = Badge.objects.search(query_string, sort_order)
        # TODO: Is this the most efficient query?
        award_list = (Award.objects.filter(badge__in=queryset))
    elif taggit and tag_name:
        tag = get_object_or_404(Tag, name=tag_name)
        queryset = (Badge.objects.filter(tags__in=[tag]).distinct())
        # TODO: Is this the most efficient query?
        award_list = (Award.objects.filter(badge__in=queryset))
    else:
        queryset = Badge.objects.order_by('-modified').all()
    return object_list(request, queryset,
        paginate_by=BADGE_PAGE_SIZE, allow_empty=True,
        extra_context=dict(
            tag_name=tag_name,
            query_string=query_string,
            award_list=award_list,
        ),
        template_object_name='badge',
        template_name='badger/badges_list.html')


@require_http_methods(['HEAD', 'GET', 'POST'])
def detail(request, slug, format="html"):
    """Badge detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_detail_by(request.user):
        return HttpResponseForbidden('Detail forbidden')

    awards = (Award.objects.filter(badge=badge)
                           .order_by('-created'))[:MAX_RECENT]

    results = detail_needs_sections.send_robust(sender=badge,
                request=request, badge=badge)
    sections = dict((x[1][0], x[1][1]) for x in results if x[1])

    if request.method == "POST":

        if request.POST.get('is_generate', None):
            if not badge.allows_manage_deferred_awards_by(request.user):
                return HttpResponseForbidden('Claim generate denied')
            amount = int(request.POST.get('amount', 10))
            reusable = (amount == 1)
            cg = badge.generate_deferred_awards(user=request.user,
                                                amount=amount,
                                                reusable=reusable)

        if request.POST.get('is_delete', None):
            if not badge.allows_manage_deferred_awards_by(request.user):
                return HttpResponseForbidden('Claim delete denied')
            group = request.POST.get('claim_group')
            badge.delete_claim_group(request.user, group)

        url = reverse('badger.views.detail', kwargs=dict(slug=slug))
        return HttpResponseRedirect(url)

    claim_groups = badge.claim_groups

    if format == 'json':
        data = badge.as_obi_serialization(request)
        resp = HttpResponse(simplejson.dumps(data))
        resp['Content-Type'] = 'application/json'
        return resp
    else:
        return render_to_response('badger/badge_detail.html', dict(
            badge=badge, award_list=awards, sections=sections,
            claim_groups=claim_groups
        ), context_instance=RequestContext(request))


@receiver(detail_needs_sections)
def _detail_award_form(sender, **kwargs):
    badge, request = kwargs['badge'], kwargs['request']
    if badge.allows_detail_by(request.user):
        return ('award', dict(
            form=BadgeAwardForm()
        ))
    else:
        return None


@require_http_methods(['GET', 'POST'])
@login_required
def award_badge(request, slug):
    """Issue an award for a badge"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_award_to(request.user):
        return HttpResponseForbidden('Award forbidden')

    if request.method != "POST":
        form = BadgeAwardForm()
    else:
        form = BadgeAwardForm(request.POST, request.FILES)
        if form.is_valid():
            emails = form.cleaned_data['emails']
            for email in emails:
                result = badge.award_to(email=email, awarder=request.user)
                if result:
                    if not hasattr(result, 'claim_code'):
                        messages.info(request, _('Award issued to %s') % email)
                    else:
                        messages.info(request, _('Invitation to claim award '
                                                 'sent to %s') % email)
            return HttpResponseRedirect(reverse('badger.views.detail', 
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
        return HttpResponseForbidden('Award detail forbidden')

    if format == 'json':
        data = simplejson.dumps(award.as_obi_assertion(request))
        resp = HttpResponse(data)
        resp['Content-Type'] = 'application/json'
        return resp
    else:
        return render_to_response('badger/award_detail.html', dict(
            badge=badge, award=award,
        ), context_instance=RequestContext(request))


@login_required
def _do_claim(request, deferred_award):
    """Perform claim of a deferred award"""
    if not deferred_award.allows_claim_by(request.user):
        return HttpResponseForbidden('Claim denied')
    award = deferred_award.claim(request.user)
    if award:
        url = reverse('badger.views.award_detail',
                      args=(award.badge.slug, award.id,))
        return HttpResponseRedirect(url)


@require_http_methods(['GET', 'POST'])
def claim_deferred_award(request, claim_code=None):
    """Deferred award detail view"""
    if not claim_code:
        claim_code = request.REQUEST.get('code', '').strip()
    deferred_award = get_object_or_404(DeferredAward, claim_code=claim_code)
    if not deferred_award.allows_detail_by(request.user):
        return HttpResponseForbidden('Claim detail denied')

    if request.method != "POST":
        grant_form = DeferredAwardGrantForm()
    else:
        grant_form = DeferredAwardGrantForm(request.POST, request.FILES)
        if not request.POST.get('is_grant', False) is not False:
            return _do_claim(request, deferred_award)
        else:
            if not deferred_award.allows_grant_by(request.user):
                return HttpResponseForbidden('Grant denied')
            if grant_form.is_valid():
                email = request.POST.get('email', None)
                deferred_award.grant_to(email=email, granter=request.user)
                messages.info(request, _('Award claim granted to %s') % email)
                url = reverse('badger.views.detail',
                              args=(deferred_award.badge.slug,))
                return HttpResponseRedirect(url)

    return render_to_response('badger/claim_deferred_award.html', dict(
        badge=deferred_award.badge, deferred_award=deferred_award,
        grant_form=grant_form
    ), context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
def claims_list(request, slug, claim_group, format="html"):
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_manage_deferred_awards_by(request.user):
        return HttpResponseForbidden()

    deferred_awards = badge.get_claim_group(claim_group) 

    if format == "pdf":
        from badger.printing import render_claims_to_pdf
        return render_claims_to_pdf(request, slug, claim_group,
                                    deferred_awards)

    return render_to_response('badger/claims_list.html', dict(
        badge=badge, claim_group=claim_group,
        deferred_awards=deferred_awards
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

@require_http_methods(['GET', 'POST'])
@login_required
def staff_tools(request):
    """HACK: This page offers miscellaneous tools useful to event staff.
    Will go away in the future, addressed by:
    https://github.com/lmorchard/django-badger/issues/35
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden()

    if request.method != "POST":
        grant_form = DeferredAwardMultipleGrantForm()
    else:
        if request.REQUEST.get('is_grant', False) is not False:
            grant_form = DeferredAwardMultipleGrantForm(request.POST, request.FILES)
            if grant_form.is_valid():
                email = grant_form.cleaned_data['email']
                codes = grant_form.cleaned_data['claim_codes']
                for claim_code in codes:
                    da = DeferredAward.objects.get(claim_code=claim_code)
                    da.grant_to(email, request.user)
                    messages.info(request, _('Badge "%s" granted to %s' %
                                             (da.badge, email)))
                url = reverse('badger.views.staff_tools')
                return HttpResponseRedirect(url)


    return render_to_response('badger/staff_tools.html', dict(
        grant_form=grant_form
    ), context_instance=RequestContext(request))
