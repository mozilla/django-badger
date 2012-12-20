import jingo
import logging
import random

from django.conf import settings

from django.http import (HttpResponseRedirect, HttpResponse,
        HttpResponseForbidden, HttpResponseNotFound)

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

from badger.models import (Award, Progress,
        BadgerException, BadgeAlreadyAwardedException,
        BadgeAwardNotAllowedException)

from badger.views import (detail_needs_sections)

from badger_multiplayer.models import (Badge, Nomination,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)

from badger_multiplayer.forms import (BadgeNewForm, BadgeEditForm,
                                      BadgeSubmitNominationForm)


@require_GET
def badges_by_user(request, username):
    """Badges created by user"""
    user = get_object_or_404(User, username=username)
    badges = Badge.objects.filter(creator=user)
    return render_to_response('badger_multiplayer/badges_by_user.html', dict(
        user=user, badge_list=badges,
    ), context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
def create(request):
    """Create a new badge"""
    if not Badge.objects.allows_add_by(request.user):
        return HttpResponseForbidden()

    if request.method != "POST":
        form = BadgeNewForm()
        form.initial['tags'] = request.GET.get('tags', '')
    else:
        form = BadgeNewForm(request.POST, request.FILES)
        if form.is_valid():
            new_sub = form.save(commit=False)
            new_sub.creator = request.user
            new_sub.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse(
                    'badger.views.detail', args=(new_sub.slug,)))

    return render_to_response('badger_multiplayer/badge_create.html', dict(
        form=form,
    ), context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
def edit(request, slug):
    """Edit an existing badge"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_edit_by(request.user):
        return HttpResponseForbidden()

    if request.method != "POST":
        form = BadgeEditForm(instance=badge)
    else:
        form = BadgeEditForm(request.POST, request.FILES, instance=badge)
        if form.is_valid():
            new_sub = form.save(commit=False)
            new_sub.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse(
                    'badger.views.detail', args=(new_sub.slug,)))

    return render_to_response('badger_multiplayer/badge_edit.html', dict(
        badge=badge, form=form,
    ), context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
def delete(request, slug):
    """Delete a badge"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_delete_by(request.user):
        return HttpResponseForbidden()

    awards_count = badge.award_set.count()

    if request.method == "POST":
        messages.info(request, _('Badge "%s" deleted.') % badge.title)
        badge.delete()
        return HttpResponseRedirect(reverse('badger.views.badges_list'))

    return render_to_response('badger_multiplayer/badge_delete.html', dict(
        badge=badge, awards_count=awards_count,
    ), context_instance=RequestContext(request))


@require_http_methods(['GET', 'POST'])
@login_required
def nomination_detail(request, slug, id, format="html"):
    """Show details on a nomination, provide for approval and acceptance"""
    badge = get_object_or_404(Badge, slug=slug)
    nomination = get_object_or_404(Nomination, badge=badge, pk=id)
    if not nomination.allows_detail_by(request.user):
        return HttpResponseForbidden()

    if request.method == "POST":
        action = request.POST.get('action', '')
        if action == 'approve_by':
            nomination.approve_by(request.user)
        elif action == 'accept':
            nomination.accept(request.user)
        return HttpResponseRedirect(reverse(
                'badger_multiplayer.views.nomination_detail',
                args=(slug, id)))

    return render_to_response('badger_multiplayer/nomination_detail.html',
                              dict(badge=badge, nomination=nomination,),
                              context_instance=RequestContext(request))


@receiver(detail_needs_sections)
def _detail_nominate_form(sender, **kwargs):
    badge, request = kwargs['badge'], kwargs['request']
    if badge.allows_nominate_for(request.user):
        return ('nominate', dict(
            form=BadgeSubmitNominationForm()
        ))
    else:
        return None


@require_http_methods(['GET', 'POST'])
@login_required
def nominate_for(request, slug):
    """Submit nomination for a badge"""
    badge = get_object_or_404(Badge, slug=slug)
    if not badge.allows_nominate_for(request.user):
        return HttpResponseForbidden()

    if request.method != "POST":
        form = BadgeSubmitNominationForm()
    else:
        form = BadgeSubmitNominationForm(request.POST, request.FILES)
        if form.is_valid():
            emails = form.cleaned_data['emails']
            for email in emails:
                users = User.objects.filter(email=email)
                if not users:
                    # TODO: Need a deferred nomination mechanism for
                    # non-registered users.
                    pass
                else:
                    nominee = users[0]
                    try:
                        award = badge.nominate_for(nominee, request.user)
                        messages.info(request,
                            _('Nomination submitted for %s') % email)
                    except BadgeAlreadyAwardedException, e:
                        messages.info(request,
                            _('Badge already awarded to %s') % email)
                    except Exception, e:
                        messages.info(request,
                            _('Nomination failed for %s') % email)

            return HttpResponseRedirect(reverse('badger.views.detail',
                                                args=(badge.slug,)))

    return render_to_response('badger_multiplayer/badge_nominate_for.html',
                              dict(form=form, badge=badge,),
                              context_instance=RequestContext(request))
