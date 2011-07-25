from django.db import models
from django.contrib.auth.models import User

from django.template.defaultfilters import slugify

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse


class GuestbookEntry(models.Model):
    """Representation of a badge"""
    message = models.TextField(blank=True)
    creator = models.ForeignKey(User, blank=False)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)
