import logging

from datetime import datetime, timedelta, tzinfo
from time import time, gmtime, strftime

from os.path import dirname

from urlparse import urljoin

from django.conf import settings

from django.db import models
from django.db.models import signals
from django.db.models.fields.files import FieldFile, ImageFieldFile
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site

from django.template.defaultfilters import slugify

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    from PIL import Image
except ImportError:
    import Image

from .signals import (badge_will_be_awarded, badge_was_awarded)


OBI_VERSION = "0.5.0"

IMG_MAX_SIZE = getattr(settings, "BADGER_IMG_MAX_SIZE", (256, 256))

SITE_ISSUER = getattr(settings, 'BADGER_SITE_ISSUER', {
    "origin": "http://mozilla.org",
    "name": "Badger",
    "org": "Mozilla",
    "contact": "lorchard@mozilla.com"
})

DEFAULT_BADGE_IMAGE = getattr(settings, 'BADGER_DEFAULT_BADGE_IMAGE',
    "%s/fixtures/default-badge.png" % dirname(__file__))

# Set up a file system for badge uploads that can be kept separate from the
# rest of /media if necessary. Lots of hackery to ensure sensible defaults.
UPLOADS_ROOT = getattr(settings, 'BADGER_UPLOADS_ROOT',
    '%suploads/' % getattr(settings, 'MEDIA_ROOT', 'media/'))
UPLOADS_URL = getattr(settings, 'BADGER_UPLOADS_URL',
    '%suploads/' % getattr(settings, 'MEDIA_URL', '/media/'))
BADGE_UPLOADS_FS = FileSystemStorage(location=UPLOADS_ROOT,
                                     base_url=UPLOADS_URL)

TIME_ZONE_OFFSET = getattr(settings, "TIME_ZONE_OFFSET", timedelta(0))


class TZOffset(tzinfo):
    """TZOffset"""

    def __init__(self, offset):
        self.offset = offset

    def utcoffset(self, dt):
        return self.offset

    def tzname(self, dt):
        return settings.TIME_ZONE

    def dst(self, dt):
        return self.offset


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

    if img.mode != "RGB":
        img = img.convert("RGB")
    new_img = StringIO()
    img.save(new_img, "PNG")
    img_data = new_img.getvalue()

    return ContentFile(img_data)


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


def mk_upload_to(field_fn):
    """upload_to builder for file upload fields"""
    def upload_to(instance, filename):
        base, slug = instance.get_upload_meta()
        time_now = int(time())
        return '%(base)s/%(slug)s_%(time_now)s_%(field_fn)s' % dict(
            time_now=time_now, slug=slug, base=base, field_fn=field_fn)
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
    add_introspection_rules([], ["^badger.model.JSONField"])
except ImportError, e:
    pass


class BadgerException(Exception):
    """General Badger model exception"""


class BadgeException(BadgerException):
    """Badge model exception"""


class BadgeAwardNotAllowedException(BadgeException):
    """Attempt to award a badge not allowed."""


class BadgeAlreadyAwardedException(BadgeException):
    """Attempt to award a unique badge twice."""


class BadgeManager(models.Manager):
    """Manager for Badge model objects"""


class Badge(models.Model):
    """Representation of a badge"""
    objects = BadgeManager()

    title = models.CharField(max_length=255, blank=False, unique=True)
    slug = models.SlugField(blank=False, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(blank=True, null=True,
                              storage=BADGE_UPLOADS_FS,
                              upload_to=mk_upload_to('image.png'))
    prerequisites = models.ManyToManyField('self', symmetrical=False,
                                            blank=True, null=True)
    unique = models.BooleanField(default=False)
    creator = models.ForeignKey(User, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    class Meta:
        unique_together = ('title', 'slug')

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
                raise ValidationError(_('Cannot process image'))
            self.image.file = scaled_file

    def save(self, **kwargs):
        """Save the submission, updating slug and screenshot thumbnails"""
        if not self.slug:
            self.slug = slugify(self.title)
        super(Badge, self).save(**kwargs)

    def allows_edit_by(self, user):
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True
        return False

    def allows_award_to(self, user):
        """Is award_to() allowed for this user?"""
        if None == user:
            return True
        if user.is_staff or user.is_superuser:
            return True
        if user == self.creator:
            return True
        return False

    def award_to(self, awardee, awarder=None):
        """Award this badge to the awardee on the awarder's behalf"""
        if not self.allows_award_to(awarder):
            raise BadgeAwardNotAllowedException()

        # If unique and already awarded, just return the existing award.
        if self.unique and self.is_awarded_to(awardee):
            return Award.objects.filter(user=awardee, badge=self)[0]

        award = Award.objects.create(user=awardee, badge=self, creator=awarder)
        return award

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

    def as_obi_serialization(self, request=None):
        """Produce an Open Badge Infrastructure serialization of this badge"""
        if request:
            base_url = request.build_absolute_uri('/')
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
            "description": self.description[:128],
            "criteria": urljoin(base_url, self.get_absolute_url()),
            "issuer": issuer
        }
        if self.image:
            data['image'] = urljoin(base_url, self.image.url)
        return data


class AwardManager(models.Manager):

    def get_query_set(self):
        return super(AwardManager, self).get_query_set().exclude(hidden=True)


class Award(models.Model):
    """Representation of a badge awarded to a user"""

    admin_objects = models.Manager()
    objects = AwardManager()

    badge = models.ForeignKey(Badge)
    image = models.ImageField(blank=True, null=True,
                              storage=BADGE_UPLOADS_FS,
                              upload_to=mk_upload_to('image.png'))
    user = models.ForeignKey(User, related_name="award_user")
    creator = models.ForeignKey(User, related_name="award_creator",
                                blank=True, null=True)
    hidden = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    def __unicode__(self):
        by = self.creator and (' by %s' % self.creator) or ''
        return u'Award of %s to %s%s' % (self.badge, self.user, by)

    @models.permalink
    def get_absolute_url(self):
        return ('badger.views.award_detail', (self.badge.slug, self.pk))

    def get_upload_meta(self):
        return ("award", self.badge.slug)

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
        # Called after super.save(), so we have some auto-gen fields like pk
        # and created
        self.bake_assertion_into_image()

        if is_new:
            # Only fire was-awarded signal on a new award.
            badge_was_awarded.send(sender=self.__class__, award=self)

            # Since this badge was just awarded, check the prerequisites on all
            # badges that count this as one.
            for dep_badge in self.badge.badge_set.all():
                dep_badge.check_prerequisites(self.user, self.badge, self)

            # Reset any progress for this user & badge upon award.
            Progress.objects.filter(user=self.user, badge=self.badge).delete()

    def as_obi_assertion(self, request=None):
        badge_data = self.badge.as_obi_serialization(request)

        if request:
            base_url = request.build_absolute_uri('/')
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

        # HACK: Coerce the creation time into a timezone and zero-out the
        # microsecond to get a nice and clean ISO8601 timestamp.
        issued_on = self.created.replace(tzinfo=TZOffset(TIME_ZONE_OFFSET),
                                         microsecond=0).isoformat()

        # see: https://github.com/brianlovesdata/openbadges/wiki/Assertions
        assertion = {
            # TODO: Get email from profile? alternate identifier?
            "recipient": self.user.email,
            "evidence": urljoin(base_url, self.get_absolute_url()),
            # "expires": "2013-06-01",
            "issued_on": issued_on,
            "badge": badge_data
        }
        return assertion

    def bake_assertion_into_image(self, request=None):
        """Bake the OBI JSON badge award assertion into a copy of the original
        badge's image, if one exists."""

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
        except IOError, e:
            return False

        # Here's where the baking gets done. JSON representation of the OBI
        # assertion gets written into the "openbadges" metadata field
        # see: http://blog.client9.com/2007/08/python-pil-and-png-metadata-take-2.html
        # see: https://github.com/brianlovesdata/openbadges/blob/master/lib/baker.js
        # see: https://github.com/brianlovesdata/openbadges/blob/master/controllers/baker.js
        from PIL import PngImagePlugin
        meta = PngImagePlugin.PngInfo()
        assertion = self.as_obi_assertion(request)
        meta.add_text('openbadges', json.dumps(assertion))

        # And, finally save out the baked image.
        new_img = StringIO()
        img.save(new_img, "PNG", pnginfo=meta)
        img_data = new_img.getvalue()
        self.image.save('', ContentFile(img_data), False)

        # Update the image field with the new image name
        # NOTE: Can't do a full save(), because this gets called in save()
        Award.objects.filter(pk=self.pk).update(image=self.image)

        return True


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
        except BadgeAlreadyAwardedException, e:
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
