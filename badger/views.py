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

from .models import (Badge, Award, Nomination,
        BadgeAwardNotAllowedException,
        NominationApproveNotAllowedException,
        NominationAcceptNotAllowedException)


BADGE_PAGE_SIZE = 12


def home(request):
    """Badger home page"""
    queryset = Badge.objects.all()
    return object_list(request, queryset,
        paginate_by=BADGE_PAGE_SIZE, allow_empty=True,
        template_object_name='badge',
        template_name='badger/home.html')


@require_GET
def detail(request, slug):
    """Badge detail view"""
    badge = get_object_or_404(Badge, slug=slug)
    return render_to_response('badger/badge_detail.html', dict(
        badge=badge,
    ), context_instance=RequestContext(request))
