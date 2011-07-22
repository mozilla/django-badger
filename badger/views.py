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

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import (BadgeNewForm, BadgeEditForm)
from .models import (Badge, Award, Nomination,
        BadgeAwardNotAllowedException,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)


def home(request):
    return render_to_response('badger/home.html', {
    }, context_instance=RequestContext(request))


def detail(request, slug):
    return render_to_response('badger/badge_detail.html', {
    }, context_instance=RequestContext(request))


@login_required
def create(request):

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

    return render_to_response('badger/badge_create.html', dict(
        form=form,
    ), context_instance=RequestContext(request))
