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

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from badger.models import (Award, Progress,
        BadgeAwardNotAllowedException)

from badger_multiplayer.models import (Badge, Nomination,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)

from badger_multiplayer.forms import (BadgeNewForm, BadgeEditForm)


@require_http_methods(['GET', 'POST'])
@login_required
def create(request):
    """Create a new badge"""
    if request.method != "POST":
        form = BadgeNewForm()
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
            new_sub.creator = request.user
            new_sub.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse(
                    'badger.views.detail', args=(new_sub.slug,)))

    return render_to_response('badger_multiplayer/badge_edit.html', dict(
        badge=badge, form=form,
    ), context_instance=RequestContext(request))
