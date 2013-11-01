import logging
import re
import random
import hashlib

from datetime import datetime, timedelta, tzinfo
from time import time, gmtime, strftime

import os.path
from os.path import dirname

from urlparse import urljoin

from django.conf import settings

from django.db import models
from django.db.models import signals, Q, Count, Max
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType

from django.template import Context, TemplateDoesNotExist
from django.template.loader import render_to_string

from django.core.serializers.json import DjangoJSONEncoder

try:
    import django.utils.simplejson as json
except ImportError: # Django 1.5 no longer bundles simplejson
    import json

# HACK: Django 1.2 is missing receiver and user_logged_in
try:
    from django.dispatch import receiver
    from django.contrib.auth.signals import user_logged_in
except ImportError:
    receiver = False
    user_logged_in = False

try:
    from tower import ugettext_lazy as _
except ImportError:
    from django.utils.translation import ugettext_lazy as _

try:
    from funfactory.urlresolvers import reverse
except ImportError:
    from django.core.urlresolvers import reverse

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from PIL import Image
except ImportError:
    import Image

try:
    import taggit
    from taggit.managers import TaggableManager
    from taggit.models import Tag, TaggedItem
except ImportError:
    taggit = None

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

import badger
from .signals import (badge_will_be_awarded, badge_was_awarded,
                      nomination_will_be_approved, nomination_was_approved,
                      nomination_will_be_accepted, nomination_was_accepted,
                      nomination_will_be_rejected, nomination_was_rejected,
                      user_will_be_nominated, user_was_nominated)


OBI_VERSION = "0.5.0"

IMG_MAX_SIZE = getattr(settings, "BADGER_IMG_MAX_SIZE", (256, 256))

SITE_ISSUER = getattr(settings, 'BADGER_SITE_ISSUER', {
    "origin": "http://mozilla.org",
    "name": "Badger",
    "org": "Mozilla",
    "contact": "lorchard@mozilla.com"
})

# Set up a file system for badge uploads that can be kept separate from the
# rest of /media if necessary. Lots of hackery to ensure sensible defaults.
UPLOADS_ROOT = getattr(settings, 'BADGER_MEDIA_ROOT',
    os.path.join(getattr(settings, 'MEDIA_ROOT', 'media/'), 'uploads'))
UPLOADS_URL = getattr(settings, 'BADGER_MEDIA_URL',
    urljoin(getattr(settings, 'MEDIA_URL', '/media/'), 'uploads/'))
BADGE_UPLOADS_FS = FileSystemStorage(location=UPLOADS_ROOT,
                                     base_url=UPLOADS_URL)

DEFAULT_BADGE_IMAGE = getattr(settings, 'BADGER_DEFAULT_BADGE_IMAGE',
    "%s/fixtures/default-badge.png" % dirname(__file__))
DEFAULT_BADGE_IMAGE_URL = getattr(settings, 'BADGER_DEFAULT_BADGE_IMAGE_URL',
    urljoin(getattr(settings, 'MEDIA_URL', '/media/'), 'img/default-badge.png'))

TIME_ZONE_OFFSET = getattr(settings, "TIME_ZONE_OFFSET", timedelta(0))

MK_UPLOAD_TMPL = '%(base)s/%(h1)s/%(h2)s/%(hash)s_%(field_fn)s_%(now)s_%(rand)04d.%(ext)s'

DEFAULT_HTTP_PROTOCOL = getattr(settings, "DEFAULT_HTTP_PROTOCOL", "http")

CLAIM_CODE_LENGTH = getattr(settings, "CLAIM_CODE_LENGTH", 6)


def _document_django_model(cls):
    """Adds meta fields to the docstring for better autodoccing"""
    fields = cls._meta.fields
    doc = cls.__doc__

    if not doc.endswith('\n\n'):
        doc = doc + '\n\n'

    for f in fields:
        doc = doc + '    :arg {0}:\n'.format(f.name)

    cls.__doc__ = doc
    return cls


def scale_image(img_upload, img_max_size):
    """Crop and scale an image file."""
    try:
        img = Image.open(img_upload)
    except IOError:
        return None

    src_width, src_height = img.size
    src_ratio = float(src_width) / float(src_height)
    dst_width, dst_height = img_max_size
    dst_ratio = float(dst_width) / float(dst_height)

    if dst_ratio < src_ratio:
        crop_height = src_height
        crop_width = crop_height * dst_ratio
        x_offset = int(float(src_width - crop_width) / 2)
        y_offset = 0
    else:
        crop_width = src_width
        crop_height = crop_width / dst_ratio
        x_offset = 0
        y_offset = int(float(src_height - crop_height) / 2)

    img = img.crop((x_offset, y_offset,
        x_offset + int(crop_width), y_offset + int(crop_height)))
    img = img.resize((dst_width, dst_height), Image.ANTIALIAS)

    # If the mode isn't RGB or RGBA we convert it. If it's not one
    # of those modes, then we don't know what the alpha channel should
    # be so we convert it to "RGB".
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    new_img = StringIO()
    img.save(new_img, "PNG")
    img_data = new_img.getvalue()

    return ContentFile(img_data)


# Taken from http://stackoverflow.com/a/4019144
def slugify(txt):
    """A custom version of slugify that retains non-ascii characters. The
    purpose of this function in the application is to make URLs more readable
    in a browser, so there are some added heuristics to retain as much of the
    title meaning as possible while excluding characters that are troublesome
    to read in URLs. For example, question marks will be seen in the browser
    URL as %3F and are thereful unreadable. Although non-ascii characters will
    also be hex-encoded in the raw URL, most browsers will display them as
    human-readable glyphs in the address bar -- those should be kept in the
    slug."""
    # remove trailing whitespace
    txt = txt.strip()
    # remove spaces before and after dashes
    txt = re.sub('\s*-\s*', '-', txt, re.UNICODE)
    # replace remaining spaces with dashes
    txt = re.sub('[\s/]', '-', txt, re.UNICODE)
    # replace colons between numbers with dashes
    txt = re.sub('(\d):(\d)', r'\1-\2', txt, re.UNICODE)
    # replace double quotes with single quotes
    txt = re.sub('"', "'", txt, re.UNICODE)
    # remove some characters altogether
    txt = re.sub(r'[?,:!@#~`+=$%^&\\*()\[\]{}<>]', '', txt, re.UNICODE)
    return txt


def get_permissions_for(self, user):
    """Mixin method to collect permissions for a model instance"""
    pre = 'allows_'
    pre_len = len(pre)
    methods = (m for m in dir(self) if m.startswith(pre))
    perms = dict(
        (m[pre_len:], getattr(self, m)(user))
        for m in methods
    )
    return perms


def mk_upload_to(field_fn, ext, tmpl=MK_UPLOAD_TMPL):
    """upload_to builder for file upload fields"""
    def upload_to(instance, filename):
        base, slug = instance.get_upload_meta()
        slug_hash = (hashlib.md5(slug.encode('utf-8', 'ignore'))
                            .hexdigest())
        return tmpl % dict(now=int(time()), rand=random.randint(0, 1000),
                           slug=slug[:50], base=base, field_fn=field_fn,
                           pk=instance.pk,
                           hash=slug_hash, h1=slug_hash[0], h2=slug_hash[1],
                           ext=ext)
    return upload_to


class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly
    see: http://djangosnippets.org/snippets/1478/
    """

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if not value:
            return dict()
        try:
            if (isinstance(value, basestring) or
                    type(value) is unicode):
                return json.loads(value)
        except ValueError:
            return dict()
        return value

    def get_db_prep_save(self, value, connection):
        """Convert our JSON object to a string before we save"""
        if not value:
            return '{}'
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        if isinstance(value, basestring) or value is None:
            return value
        return smart_unicode(value)


# Tell South that this field isn't all that special
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^badger.models.JSONField"])
except ImportError:
    pass


class SearchManagerMixin(object):
    """Quick & dirty manager mixin for search"""

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _normalize_query(self, query_string,
                        findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                        normspace=re.compile(r'\s{2,}').sub):
        """
        Splits the query string in invidual keywords, getting rid of unecessary spaces
        and grouping quoted words together.
        Example::

            foo._normalize_query('  some random  words "with   quotes  " and   spaces')
            ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

        """
        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

    # See: http://www.julienphalip.com/blog/2008/08/16/adding-search-django-site-snap/
    def _get_query(self, query_string, search_fields):
        """
        Returns a query, that is a combination of Q objects. That
        combination aims to search keywords within a model by testing
        the given search fields.

        """
        query = None  # Query to search for every search term
        terms = self._normalize_query(query_string)
        for term in terms:
            or_query = None  # Query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    def search(self, query_string, sort='title'):
        """Quick and dirty keyword search on submissions"""
        # TODO: Someday, replace this with something like Sphinx or another real
        # search engine
        strip_qs = query_string.strip()
        if not strip_qs:
            return self.all_sorted(sort).order_by('-modified')
        else:
            query = self._get_query(strip_qs, self.search_fields)
            return self.all_sorted(sort).filter(query).order_by('-modified')

    def all_sorted(self, sort=None):
        """Apply to .all() one of the sort orders supported for views"""
        queryset = self.all()
        if sort == 'title':
            return queryset.order_by('title')
        else:
            return queryset.order_by('-created')


class BadgerException(Exception):
    """General Badger model exception"""


class BadgeException(BadgerException):
    """Badge model exception"""


class BadgeAwardNotAllowedException(BadgeException):
    """Attempt to award a badge not allowed."""


class BadgeAlreadyAwardedException(BadgeException):
    """Attempt to award a unique badge twice."""


class BadgeDeferredAwardManagementNotAllowedException(BadgeException):
    """Attempt to manage deferred awards not allowed."""


class BadgeManager(models.Manager, SearchManagerMixin):
    """Manager for Badge model objects"""
    search_fields = ('title', 'slug', 'description', )

    def allows_add_by(self, user):
        if user.is_anonymous():
            return False
        if getattr(settings, "BADGER_ALLOW_ADD_BY_ANYONE", False):
            return True
        if user.has_perm('badger.add_badge'):
            return True
        return False

    def allows_grant_by(self, user):
        if user.is_anonymous():
            return False
        if user.has_perm('badger.grant_deferredaward'):
            return True
        return False

    def top_tags(self, min_count=2, limit=20):
        """Assemble list of top-used tags"""
        if not taggit:
            return []

        # TODO: There has got to be a better way to do this. I got lost in
        # Django model bits, though.

        # Gather list of tags sorted by use frequency
        ct = ContentType.objects.get_for_model(Badge)
        tag_counts = (TaggedItem.objects
            .values('tag')
            .annotate(count=Count('id'))
            .filter(content_type=ct, count__gte=min_count)
            .order_by('-count'))[:limit]

        # Gather set of tag IDs from list
        tag_ids = set(x['tag'] for x in tag_counts)

        # Gather and map tag objects to IDs
        tags_by_id = dict((x.pk, x)
            for x in Tag.objects.filter(pk__in=tag_ids))

        # Join tag objects up with counts
        tags_with_counts = [
            dict(count=x['count'], tag=tags_by_id[x['tag']])
            for x in tag_counts]

        return tags_with_counts


@_document_django_model
class Badge(models.Model):
    """Representation of a badge"""
    objects = BadgeManager()

    title = models.CharField(max_length=255, blank=False, unique=True,
        help_text='Short, descriptive title')
    slug = models.SlugField(blank=False, unique=True,
        help_text='Very short name, for use in URLs and links')
    description = models.TextField(blank=True,
        help_text='Longer description of the badge and its criteria')
    image = models.ImageField(blank=True, null=True,
            storage=BADGE_UPLOADS_FS, upload_to=mk_upload_to('image', 'png'),
            help_text='Upload an image to represent the badge')
    prerequisites = models.ManyToManyField('self', symmetrical=False,
            blank=True, null=True,
            help_text=('When all of the selected badges have been awarded, this '
                       'badge will be automatically awarded.'))
    # TODO: Rename? Eventually we'll want a globally-unique badge. That is, one
    # unique award for one person for the whole site.
    unique = models.BooleanField(default=True,
            help_text=('Should awards of this badge be limited to '
                       'one-per-person?'))

    nominations_accepted = models.BooleanField(default=True, blank=True,
            help_text=('Should this badge accept nominations from '
                       'other users?'))

    nominations_autoapproved = models.BooleanField(default=False, blank=True,
            help_text='Should all nominations be automatically approved?')

    if taggit:
        tags = TaggableManager(blank=True)

    creator = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    class Meta:
        unique_together = ('title', 'slug')
        ordering = ['-modified', '-created']
        permissions = (
            ('manage_deferredawards',
             _(u'Can manage deferred awards for this badge')),
        )

    get_permissions_for = get_permissions_for

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('badger.views.detail', args=(self.slug,))

    def get_upload_meta(self):
        return ("badge", self.slug)

    def clean(self):
        if self.image:
            scaled_file = scale_image(self.image.file, IMG_MAX_SIZE)
            if not scaled_file:
                raise ValidationError(_(u'Cannot process image'))
            self.image.file = scaled_file

    def save(self, **kwargs):
        """Save the submission, updating slug and screenshot thumbnails"""
        if not self.slug:
            self.slug = slugify(self.title)

        super(Badge, self).save(**kwargs)

        if notification:
            if self.creator:
                notification.send([self.creator], 'badge_edited',
                                  dict(badge=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))

    def delete(self, **kwargs):
        """Make sure deletes cascade to awards"""
        self.award_set.all().delete()
        super(Badge, self).delete(**kwargs)

    def allows_detail_by(self, user):
        # TODO: Need some logic here, someday.
        return True

    def allows_edit_by(self, user):
        if user.is_anonymous():
            return False
        if user.has_perm('badger.change_badge'):
            return True
        if user == self.creator:
            return True
        return False

    def allows_delete_by(self, user):
        if user.is_anonymous():
            return False
        if user.has_perm('badger.change_badge'):
            return True
        if user == self.creator:
            return True
        return False

    def allows_award_to(self, user):
        """Is award_to() allowed for this user?"""
        if None == user:
            return True
        if user.is_anonymous():
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True

        # TODO: List of delegates for whom awarding is allowed

        return False

    def allows_manage_deferred_awards_by(self, user):
        """Can this user manage deferred awards"""
        if user.is_anonymous():
            return False
        if user.has_perm('badger.manage_deferredawards'):
            return True
        if user == self.creator:
            return True
        return False

    def generate_deferred_awards(self, user, amount=10, reusable=False):
        """Generate a number of deferred awards with a claim group code"""
        if not self.allows_manage_deferred_awards_by(user):
            raise BadgeDeferredAwardManagementNotAllowedException()
        return (DeferredAward.objects.generate(self, user, amount, reusable))

    def get_claim_group(self, claim_group):
        """Get all the deferred awards for a claim group code"""
        return DeferredAward.objects.filter(claim_group=claim_group)

    def delete_claim_group(self, user, claim_group):
        """Delete all the deferred awards for a claim group code"""
        if not self.allows_manage_deferred_awards_by(user):
            raise BadgeDeferredAwardManagementNotAllowedException()
        self.get_claim_group(claim_group).delete()

    @property
    def claim_groups(self):
        """Produce a list of claim group IDs available"""
        return DeferredAward.objects.get_claim_groups(badge=self)

    def award_to(self, awardee=None, email=None, awarder=None,
                 description='', raise_already_awarded=False):
        """Award this badge to the awardee on the awarder's behalf"""
        # If no awarder given, assume this is on the badge creator's behalf.
        if not awarder:
            awarder = self.creator

        if not self.allows_award_to(awarder):
            raise BadgeAwardNotAllowedException()

        # If we have an email, but no awardee, try looking up the user.
        if email and not awardee:
            qs = User.objects.filter(email=email)
            if not qs:
                # If there's no user for this email address, create a
                # DeferredAward for future claiming.

                if self.unique and DeferredAward.objects.filter(
                    badge=self, email=email).exists():
                    raise BadgeAlreadyAwardedException()

                da = DeferredAward(badge=self, email=email)
                da.save()
                return da

            # Otherwise, we'll use the most recently created user
            awardee = qs.latest('date_joined')

        if self.unique and self.is_awarded_to(awardee):
            if raise_already_awarded:
                raise BadgeAlreadyAwardedException()
            else:
                return Award.objects.filter(user=awardee, badge=self)[0]

        return Award.objects.create(user=awardee, badge=self,
                                    creator=awarder,
                                    description=description)

    def check_prerequisites(self, awardee, dep_badge, award):
        """Check the prerequisites for this badge. If they're all met, award
        this badge to the user."""
        if self.is_awarded_to(awardee):
            # Not unique, but badge auto-award from prerequisites should only
            # happen once.
            return None
        for badge in self.prerequisites.all():
            if not badge.is_awarded_to(awardee):
                # Bail on the first unmet prerequisites
                return None
        return self.award_to(awardee)

    def is_awarded_to(self, user):
        """Has this badge been awarded to the user?"""
        return Award.objects.filter(user=user, badge=self).count() > 0

    def progress_for(self, user):
        """Get or create (but not save) a progress record for a user"""
        try:
            # Look for an existing progress record...
            p = Progress.objects.get(user=user, badge=self)
        except Progress.DoesNotExist:
            # If none found, create a new one but don't save it yet.
            p = Progress(user=user, badge=self)
        return p

    def allows_nominate_for(self, user):
        """Is nominate_for() allowed for this user?"""
        if not self.nominations_accepted:
            return False
        if None == user:
            return True
        if user.is_anonymous():
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True

        # TODO: Flag to enable / disable nominations from anyone
        # TODO: List of delegates from whom nominations are accepted

        return True

    def nominate_for(self, nominee, nominator=None):
        """Nominate a nominee for this badge on the nominator's behalf"""
        nomination = Nomination.objects.create(badge=self, creator=nominator,
                                         nominee=nominee)
        if notification:
            if self.creator:
                notification.send([self.creator], 'nomination_submitted',
                                  dict(nomination=nomination,
                                       protocol=DEFAULT_HTTP_PROTOCOL))

        if self.nominations_autoapproved:
            nomination.approve_by(self.creator)

        return nomination

    def is_nominated_for(self, user):
        return Nomination.objects.filter(nominee=user, badge=self).count() > 0

    def as_obi_serialization(self, request=None):
        """Produce an Open Badge Infrastructure serialization of this badge"""
        if request:
            base_url = request.build_absolute_uri('/')[:-1]
        else:
            base_url = 'http://%s' % (Site.objects.get_current().domain,)

        # see: https://github.com/brianlovesdata/openbadges/wiki/Assertions
        if not self.creator:
            issuer = SITE_ISSUER
        else:
            issuer = {
                # TODO: Get from user profile instead?
                "origin": urljoin(base_url, self.creator.get_absolute_url()),
                "name": self.creator.username,
                "contact": self.creator.email
            }

        data = {
            # The version of the spec/hub this manifest is compatible with. Use
            # "0.5.0" for the beta.
            "version": OBI_VERSION,
            # TODO: truncate more intelligently
            "name": self.title[:128],
            # TODO: truncate more intelligently
            "description": self.description[:128] or self.title[:128],
            "criteria": urljoin(base_url, self.get_absolute_url()),
            "issuer": issuer
        }

        image_url = self.image and self.image.url or DEFAULT_BADGE_IMAGE_URL
        data['image'] = urljoin(base_url, image_url)

        return data


class AwardManager(models.Manager):
    def get_query_set(self):
        return super(AwardManager, self).get_query_set().exclude(hidden=True)


@_document_django_model
class Award(models.Model):
    """Representation of a badge awarded to a user"""

    admin_objects = models.Manager()
    objects = AwardManager()

    description = models.TextField(blank=True,
            help_text='Explanation and evidence for the badge award')
    badge = models.ForeignKey(Badge)
    image = models.ImageField(blank=True, null=True,
                              storage=BADGE_UPLOADS_FS,
                              upload_to=mk_upload_to('image', 'png'))
    claim_code = models.CharField(max_length=32, blank=True,
            default='', unique=False, db_index=True,
            help_text='Code used to claim this award')
    user = models.ForeignKey(User, related_name="award_user")
    creator = models.ForeignKey(User, related_name="award_creator",
                                blank=True, null=True)
    hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    class Meta:
        ordering = ['-modified', '-created']

    def __unicode__(self):
        by = self.creator and (u' by %s' % self.creator) or u''
        return u'Award of %s to %s%s' % (self.badge, self.user, by)

    @models.permalink
    def get_absolute_url(self):
        return ('badger.views.award_detail', (self.badge.slug, self.pk))

    def get_upload_meta(self):
        u = self.user.username
        return ("award/%s/%s/%s" % (u[0], u[1], u), self.badge.slug)

    def allows_detail_by(self, user):
        # TODO: Need some logic here, someday.
        return True

    def allows_delete_by(self, user):
        if user.is_anonymous():
            return False
        if user == self.user:
            return True
        if user == self.creator:
            return True
        if user.has_perm('badger.change_award'):
            return True
        return False

    def save(self, *args, **kwargs):

        # Signals and some bits of logic only happen on a new award.
        is_new = not self.pk

        if is_new:
            # Bail if this is an attempt to double-award a unique badge
            if self.badge.unique and self.badge.is_awarded_to(self.user):
                raise BadgeAlreadyAwardedException()

            # Only fire will-be-awarded signal on a new award.
            badge_will_be_awarded.send(sender=self.__class__, award=self)

        super(Award, self).save(*args, **kwargs)

        # Called after super.save(), so we have some auto-gen fields
        if badger.settings.BAKE_AWARD_IMAGES:
            self.bake_obi_image()

        if is_new:
            # Only fire was-awarded signal on a new award.
            badge_was_awarded.send(sender=self.__class__, award=self)

            if notification:
                if self.creator:
                    notification.send([self.badge.creator], 'badge_awarded',
                                      dict(award=self,
                                           protocol=DEFAULT_HTTP_PROTOCOL))
                notification.send([self.user], 'award_received',
                                  dict(award=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))

            # Since this badge was just awarded, check the prerequisites on all
            # badges that count this as one.
            for dep_badge in self.badge.badge_set.all():
                dep_badge.check_prerequisites(self.user, self.badge, self)

            # Reset any progress for this user & badge upon award.
            Progress.objects.filter(user=self.user, badge=self.badge).delete()

    def delete(self):
        """Make sure nominations get deleted along with awards"""
        Nomination.objects.filter(award=self).delete()
        super(Award, self).delete()

    def as_obi_assertion(self, request=None):
        badge_data = self.badge.as_obi_serialization(request)

        if request:
            base_url = request.build_absolute_uri('/')[:-1]
        else:
            base_url = 'http://%s' % (Site.objects.get_current().domain,)

        # If this award has a creator (ie. not system-issued), tweak the issuer
        # data to reflect award creator.
        # TODO: Is this actually a good idea? Or should issuer be site-wide
        if self.creator:
            badge_data['issuer'] = {
                # TODO: Get from user profile instead?
                "origin": base_url,
                "name": self.creator.username,
                "contact": self.creator.email
            }

        # see: https://github.com/brianlovesdata/openbadges/wiki/Assertions
        # TODO: This salt is stable, and the badge.pk is generally not
        # disclosed anywhere, but is it obscured enough?
        hash_salt = (hashlib.md5('%s-%s' % (self.badge.pk, self.pk))
                            .hexdigest())
        recipient_text = '%s%s' % (self.user.email, hash_salt)
        recipient_hash = ('sha256$%s' % hashlib.sha256(recipient_text)
                                               .hexdigest())
        assertion = {
            "recipient": recipient_hash,
            "salt": hash_salt,
            "evidence": urljoin(base_url, self.get_absolute_url()),
            # TODO: implement award expiration
            # "expires": self.expires.date().isoformat(),
            "issued_on": self.created.date().isoformat(),
            "badge": badge_data
        }
        return assertion

    def bake_obi_image(self, request=None):
        """Bake the OBI JSON badge award assertion into a copy of the original
        badge's image, if one exists."""

        if request:
            base_url = request.build_absolute_uri('/')
        else:
            base_url = 'http://%s' % (Site.objects.get_current().domain,)

        if self.badge.image:
            # Make a duplicate of the badge image
            self.badge.image.open()
            img_copy_fh = StringIO(self.badge.image.file.read())
        else:
            # Make a copy of the default badge image
            img_copy_fh = StringIO(open(DEFAULT_BADGE_IMAGE, 'rb').read())

        try:
            # Try processing the image copy, bail if the image is bad.
            img = Image.open(img_copy_fh)
        except IOError:
            return False

        # Here's where the baking gets done. JSON representation of the OBI
        # assertion gets written into the "openbadges" metadata field
        # see: http://blog.client9.com/2007/08/python-pil-and-png-metadata-take-2.html
        # see: https://github.com/mozilla/openbadges/blob/development/lib/baker.js
        # see: https://github.com/mozilla/openbadges/blob/development/controllers/baker.js
        try:
            from PIL import PngImagePlugin
        except ImportError:
            import PngImagePlugin
        meta = PngImagePlugin.PngInfo()

        # TODO: Will need this, if we stop doing hosted assertions
        # assertion = self.as_obi_assertion(request)
        # meta.add_text('openbadges', json.dumps(assertion))
        hosted_assertion_url = '%s%s' % (
            base_url, reverse('badger.award_detail_json',
                              args=(self.badge.slug, self.id)))
        meta.add_text('openbadges', hosted_assertion_url)

        # And, finally save out the baked image.
        new_img = StringIO()
        img.save(new_img, "PNG", pnginfo=meta)
        img_data = new_img.getvalue()
        name_before = self.image.name
        self.image.save('', ContentFile(img_data), False)
        if (self.image.storage.exists(name_before)):
            self.image.storage.delete(name_before)

        # Update the image field with the new image name
        # NOTE: Can't do a full save(), because this gets called in save()
        Award.objects.filter(pk=self.pk).update(image=self.image)

        return True

    @property
    def nomination(self):
        """Find the nomination behind this award, if any."""
        # TODO: This should really be a foreign key relation, someday.
        try:
            return Nomination.objects.get(award=self)
        except Nomination.DoesNotExist:
            return None


class ProgressManager(models.Manager):
    pass


class Progress(models.Model):
    """Record tracking progress toward auto-award of a badge"""
    badge = models.ForeignKey(Badge)
    user = models.ForeignKey(User, related_name="progress_user")
    percent = models.FloatField(default=0)
    counter = models.FloatField(default=0, blank=True, null=True)
    notes = JSONField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    class Meta:
        unique_together = ('badge', 'user')
        verbose_name_plural = "Progresses"

    get_permissions_for = get_permissions_for

    def __unicode__(self):
        perc = self.percent and (' (%s%s)' % (self.percent, '%')) or ''
        return u'Progress toward %s by %s%s' % (self.badge, self.user, perc)

    def save(self, *args, **kwargs):
        """Save the progress record, with before and after signals"""
        # Signals and some bits of logic only happen on a new award.
        is_new = not self.pk

        # Bail if this is an attempt to double-award a unique badge
        if (is_new and self.badge.unique and
                self.badge.is_awarded_to(self.user)):
            raise BadgeAlreadyAwardedException()

        super(Progress, self).save(*args, **kwargs)

        # If the percent is over/equal to 1.0, auto-award on save.
        if self.percent >= 100:
            self.badge.award_to(self.user)

    def _quiet_save(self, raise_exception=False):
        try:
            self.save()
        except BadgeAlreadyAwardedException as e:
            if raise_exception:
                raise e

    def update_percent(self, current, total=None, raise_exception=False):
        """Update the percent completion value."""
        if total is None:
            value = current
        else:
            value = (float(current) / float(total)) * 100.0
        self.percent = value
        self._quiet_save(raise_exception)

    def increment_by(self, amount, raise_exception=False):
        # TODO: Do this with an UPDATE counter+amount in DB
        self.counter += amount
        self._quiet_save(raise_exception)
        return self

    def decrement_by(self, amount, raise_exception=False):
        # TODO: Do this with an UPDATE counter-amount in DB
        self.counter -= amount
        self._quiet_save(raise_exception)
        return self


class DeferredAwardManager(models.Manager):

    def get_claim_groups(self, badge):
        """Build a list of all known claim group IDs for a badge"""
        qs = (self.filter(badge=badge)
                    .values('claim_group').distinct().all()
                    .annotate(modified=Max('modified'), count=Count('id')))
        return [x
                for x in qs
                if x['claim_group']]

    def generate(self, badge, user=None, amount=10, reusable=False):
        """Generate a number of deferred awards for a badge"""
        claim_group = '%s-%s' % (time(), random.randint(0, 10000))
        for i in range(0, amount):
            (DeferredAward(badge=badge, creator=user, reusable=reusable,
                           claim_group=claim_group).save())
        return claim_group

    def claim_by_email(self, awardee):
        """Claim all deferred awards that match the awardee's email"""
        return self._claim_qs(awardee, self.filter(email=awardee.email))

    def claim_by_code(self, awardee, code):
        """Claim a deferred award by code for the awardee"""
        return self._claim_qs(awardee, self.filter(claim_code=code))

    def _claim_qs(self, awardee, qs):
        """Claim all the deferred awards that match the queryset"""
        for da in qs:
            da.claim(awardee)


def make_random_code():
    """Generare a random code, using a set of alphanumeric characters that
    attempts to avoid ambiguously similar shapes."""
    s = '3479acefhjkmnprtuvwxy'
    return ''.join([random.choice(s) for x in range(CLAIM_CODE_LENGTH)])


class DeferredAwardGrantNotAllowedException(BadgerException):
    """Attempt to grant a DeferredAward not allowed"""


@_document_django_model
class DeferredAward(models.Model):
    """Deferred award, can be converted into into a real award."""
    objects = DeferredAwardManager()

    badge = models.ForeignKey(Badge)
    description = models.TextField(blank=True)
    reusable = models.BooleanField(default=False)
    email = models.EmailField(blank=True, null=True, db_index=True)
    claim_code = models.CharField(max_length=32,
            default=make_random_code, unique=True, db_index=True)
    claim_group = models.CharField(max_length=32, blank=True, null=True,
            db_index=True)
    creator = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    class Meta:
        ordering = ['-modified', '-created']
        permissions = (
            ("grant_deferredaward",
             _(u'Can grant deferred award to an email address')),
        )

    get_permissions_for = get_permissions_for

    def allows_detail_by(self, user):
        # TODO: Need some logic here, someday.
        return True

    def allows_claim_by(self, user):
        if user.is_anonymous():
            return False
        # TODO: Need some logic here, someday.
        # TODO: Could enforce that the user.email == self.email, but I want to
        # allow for people with multiple email addresses. That is, I get an
        # award claim invite sent to lorchard@mozilla.com, but I claim it while
        # signed in as me@lmorchard.com. Warning displayed in the view.
        return True

    def allows_grant_by(self, user):
        if user.is_anonymous():
            return False
        if user.has_perm('badger.grant_deferredaward'):
            return True
        if self.badge.allows_award_to(user):
            return True
        if user == self.creator:
            return True
        return False

    def get_claim_url(self):
        """Get the URL to a page where this DeferredAward can be claimed."""
        return reverse('badger.views.claim_deferred_award',
                       args=(self.claim_code,))

    def save(self, **kwargs):
        """Save the DeferredAward, sending a claim email if it's new"""
        is_new = not self.pk
        has_existing_deferreds = False
        if self.email:
            has_existing_deferreds = DeferredAward.objects.filter(
                email=self.email).exists()

        super(DeferredAward, self).save(**kwargs)

        if is_new and self.email and not has_existing_deferreds:
            try:
                # If this is new and there's an email, send an invite to claim.
                context = Context(dict(
                    deferred_award=self,
                    badge=self.badge,
                    protocol=DEFAULT_HTTP_PROTOCOL,
                    current_site=Site.objects.get_current()
                ))
                tmpl_name = 'badger/deferred_award_%s.txt'
                subject = render_to_string(tmpl_name % 'subject', {}, context)
                # Email subjects can't contain newlines, so we strip it. It makes
                # the template less fragile.
                subject = subject.strip()
                body = render_to_string(tmpl_name % 'body', {}, context)
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                          [self.email], fail_silently=False)
            except TemplateDoesNotExist:
                pass

    def claim(self, awardee):
        """Claim the deferred award for the given user"""
        try:
            award = self.badge.award_to(awardee=awardee, awarder=self.creator)
            award.claim_code = self.claim_code
            award.save()
        except (BadgeAlreadyAwardedException, BadgeAwardNotAllowedException):
            # Just swallow up and ignore any issues in awarding.
            award = None
        if not self.reusable:
            # Self-destruct, if not made reusable.
            self.delete()
        return award

    def grant_to(self, email, granter):
        """Grant this deferred award to the given email"""
        if not self.allows_grant_by(granter):
            raise DeferredAwardGrantNotAllowedException()
        if not self.reusable:
            # If not reusable, reassign email and regenerate claim code.
            self.email = email
            self.claim_code = make_random_code()
            self.save()
            return self
        else:
            # If reusable, create a clone and leave this deferred award alone.
            new_da = DeferredAward(badge=self.badge, email=email,
                                   creator=granter, reusable=False)
            new_da.save()
            return new_da


class NominationException(BadgerException):
    """Nomination model exception"""


class NominationApproveNotAllowedException(NominationException):
    """Attempt to approve a nomination was disallowed"""


class NominationAcceptNotAllowedException(NominationException):
    """Attempt to accept a nomination was disallowed"""


class NominationRejectNotAllowedException(NominationException):
    """Attempt to reject a nomination was disallowed"""


class NominationManager(models.Manager):
    pass


@_document_django_model
class Nomination(models.Model):
    """Representation of a user nominated by another user for a badge"""
    objects = NominationManager()

    badge = models.ForeignKey(Badge)
    nominee = models.ForeignKey(User, related_name="nomination_nominee",
            blank=False, null=False)
    accepted = models.BooleanField(default=False)
    creator = models.ForeignKey(User, related_name="nomination_creator",
            blank=True, null=True)
    approver = models.ForeignKey(User, related_name="nomination_approver",
            blank=True, null=True)
    rejected_by = models.ForeignKey(User, related_name="nomination_rejected_by",
            blank=True, null=True)
    rejected_reason = models.TextField(blank=True)
    award = models.ForeignKey(Award, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    def __unicode__(self):
        return u'Nomination for %s to %s by %s' % (self.badge, self.nominee,
                                                   self.creator)

    def get_absolute_url(self):
        return reverse('badger.views.nomination_detail',
                       args=(self.badge.slug, self.id))

    def save(self, *args, **kwargs):

        # Signals and some bits of logic only happen on a new nomination.
        is_new = not self.pk

        # Bail if this is an attempt to double-award a unique badge
        if (is_new and self.badge.unique and
                self.badge.is_awarded_to(self.nominee)):
            raise BadgeAlreadyAwardedException()

        if is_new:
            user_will_be_nominated.send(sender=self.__class__,
                                        nomination=self)

        if self.is_approved and self.is_accepted:
            self.award = self.badge.award_to(self.nominee, self.approver)

        super(Nomination, self).save(*args, **kwargs)

        if is_new:
            user_was_nominated.send(sender=self.__class__,
                                    nomination=self)

    def allows_detail_by(self, user):
        if (user.is_staff or
               user.is_superuser or
               user == self.badge.creator or
               user == self.nominee or
               user == self.creator):
            return True

        # TODO: List of delegates empowered by badge creator to approve nominations

        return False

    @property
    def is_approved(self):
        """Has this nomination been approved?"""
        return self.approver is not None

    def allows_approve_by(self, user):
        if self.is_approved or self.is_rejected:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user == self.badge.creator:
            return True

        # TODO: List of delegates empowered by badge creator to approve nominations

        return False

    def approve_by(self, approver):
        """Approve this nomination.
        Also awards, if already accepted."""
        if not self.allows_approve_by(approver):
            raise NominationApproveNotAllowedException()
        self.approver = approver
        nomination_will_be_approved.send(sender=self.__class__,
                                         nomination=self)
        self.save()
        nomination_was_approved.send(sender=self.__class__,
                                     nomination=self)
        if notification:
            if self.badge.creator:
                notification.send([self.badge.creator], 'nomination_approved',
                                  dict(nomination=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))
            if self.creator:
                notification.send([self.creator], 'nomination_approved',
                                  dict(nomination=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))
            notification.send([self.nominee], 'nomination_received',
                              dict(nomination=self,
                                   protocol=DEFAULT_HTTP_PROTOCOL))

        return self

    @property
    def is_accepted(self):
        """Has this nomination been accepted?"""
        return self.accepted

    def allows_accept(self, user):
        if self.is_accepted or self.is_rejected:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user == self.nominee:
            return True
        return False

    def accept(self, user):
        """Accept this nomination for the nominee.

        Also awards, if already approved.
        """
        if not self.allows_accept(user):
            raise NominationAcceptNotAllowedException()
        self.accepted = True
        nomination_will_be_accepted.send(sender=self.__class__,
                                         nomination=self)
        self.save()
        nomination_was_accepted.send(sender=self.__class__,
                                     nomination=self)

        if notification:
            if self.badge.creator:
                notification.send([self.badge.creator], 'nomination_accepted',
                                  dict(nomination=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))
            if self.creator:
                notification.send([self.creator], 'nomination_accepted',
                                  dict(nomination=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))

        return self

    @property
    def is_rejected(self):
        """Has this nomination been rejected?"""
        return self.rejected_by is not None

    def allows_reject_by(self, user):
        if self.is_approved or self.is_rejected:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user == self.nominee:
            return True
        if user == self.badge.creator:
            return True
        return False

    def reject_by(self, user, reason=''):
        if not self.allows_reject_by(user):
            raise NominationRejectNotAllowedException()
        self.rejected_by = user
        self.rejected_reason = reason
        nomination_will_be_rejected.send(sender=self.__class__,
                                         nomination=self)
        self.save()
        nomination_was_rejected.send(sender=self.__class__,
                                     nomination=self)

        if notification:
            if self.badge.creator:
                notification.send([self.badge.creator], 'nomination_rejected',
                                  dict(nomination=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))
            if self.creator:
                notification.send([self.creator], 'nomination_rejected',
                                  dict(nomination=self,
                                       protocol=DEFAULT_HTTP_PROTOCOL))

        return self


# HACK: Django 1.2 is missing receiver and user_logged_in
if receiver and user_logged_in:
    @receiver(user_logged_in)
    def claim_on_login(sender, request, user, **kwargs):
        """When a user logs in, claim any deferred awards by email"""
        DeferredAward.objects.claim_by_email(user)
