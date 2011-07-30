from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.contrib.auth.models import User, AnonymousUser

from django.template.defaultfilters import slugify

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

from .signals import (user_will_be_nominated, user_was_nominated,
                      nomination_will_be_approved, nomination_was_approved,
                      nomination_will_be_accepted, nomination_was_accepted,
                      badge_will_be_awarded, badge_was_awarded)


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


class BadgeManager(models.Manager):
    """Manager for Badge model objects"""


class Badge(models.Model):
    """Representation of a badge"""
    objects = BadgeManager()

    title = models.CharField(max_length=255, blank=False, unique=True)
    slug = models.SlugField(blank=False, unique=True)
    description = models.TextField(blank=True)
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
        return u'<Badge %s>' % self.title

    def get_absolute_url(self):
        return reverse('badger.views.detail', args=[self.slug])

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

    def award_to(self, awardee, awarder=None, nomination=None):
        """Award this badge to the awardee on the awarder's behalf, with an
        optional nomination involved"""
        if not self.allows_award_to(awarder):
            raise BadgeAwardNotAllowedException()

        if self.unique and self.is_awarded_to(awardee):
            # Attempt to double-award a unique badge just results in the
            # existing award being returned. But, no signal fires.
            return Award.objects.filter(user=awardee, badge=self)[0]

        award = Award(user=awardee, badge=self, creator=awarder,
                nomination=nomination)

        badge_will_be_awarded.send(sender=self.__class__, award=award)
        award.save()
        badge_was_awarded.send(sender=self.__class__, award=award)

        # Since this badge was just awarded, check the prerequisites on all
        # badges that count this as one.
        for dep_badge in self.badge_set.all():
            dep_badge.check_prerequisites(awardee, self, award)

        return award

    def check_prerequisites(self, awardee, dep_badge, award):
        """Check the prerequisites for this badge. If they're all met, award
        this badge to the user."""
        for badge in self.prerequisites.all():
            if not badge.is_awarded_to(awardee):
                # Bail on the first unmet prerequisites
                return None
        return self.award_to(awardee)

    def is_awarded_to(self, user):
        """Has this badge been awarded to the user?"""
        return Award.objects.filter(user=user, badge=self).count() > 0

    def nominate_for(self, nominator, nominee):
        """Nominate a nominee for this badge on the nominator's behalf"""
        nomination = Nomination(badge=self, creator=nominator, nominee=nominee)
        user_will_be_nominated.send(sender=self.__class__,
                                    nomination=nomination)
        nomination.save()
        user_was_nominated.send(sender=self.__class__, nomination=nomination)
        return nomination

    def is_nominated_for(self, user):
        return Nomination.objects.filter(nominee=user, badge=self).count() > 0

    def progress_for(self, user):
        """Get or create (but not save) a progress record for a user"""
        try:
            # Look for an existing progress record...
            p = Progress.objects.get(user=user, badge=self)
        except Progress.DoesNotExist:
            # If none found, create a new one but don't save it yet.
            p = Progress(user=user, badge=self)
        return p


class NominationException(BadgerException):
    """Nomination model exception"""


class NominationApproveNotAllowedException(NominationException):
    """Attempt to approve a nomination was disallowed"""


class NominationAcceptNotAllowedException(NominationException):
    """Attempt to accept a nomination was disallowed"""


class NominationManager(models.Manager):
    pass


class Nomination(models.Model):
    """Representation of a user nominated by another user for a badge"""
    objects = NominationManager()

    badge = models.ForeignKey(Badge)
    nominee = models.ForeignKey(User, related_name="nomination_nominee",
            blank=False, null=False)
    accepted = models.BooleanField(default=False)
    creator = models.ForeignKey(User, related_name="nomination_creator",
            blank=False, null=False)
    approver = models.ForeignKey(User, related_name="nomination_approver",
            blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    def allows_approve_by(self, user):
        if user.is_staff or user.is_superuser:
            return True
        if user == self.badge.creator:
            return True
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
        self._award_if_ready()
        nomination_was_approved.send(sender=self.__class__,
                                     nomination=self)
        return self

    def is_approved(self):
        """Has this nomination been approved?"""
        return self.approver is not None

    def allows_accept(self, user):
        if user.is_staff or user.is_superuser:
            return True
        if user == self.nominee:
            return True
        return False

    def accept(self, user):
        """Accept this nomination for the nominee.
        Also awards, if already approved."""
        if not self.allows_accept(user):
            raise NominationAcceptNotAllowedException()
        self.accepted = True
        nomination_will_be_accepted.send(sender=self.__class__,
                                         nomination=self)
        self.save()
        self._award_if_ready()
        nomination_was_accepted.send(sender=self.__class__,
                                     nomination=self)
        return self

    def is_accepted(self):
        """Has this nomination been accepted?"""
        return self.accepted

    def _award_if_ready(self):
        """If approved and accepted, award the badge to nominee on
        behalf of approver."""
        if self.is_approved() and self.is_accepted():
            self.badge.award_to(self.nominee, self.approver, self)


class AwardManager(models.Manager):
    pass


class Award(models.Model):
    """Representation of a badge awarded to a user"""
    objects = AwardManager()

    badge = models.ForeignKey(Badge)
    user = models.ForeignKey(User, related_name="award_user")
    nomination = models.ForeignKey(Nomination, blank=True, null=True)
    creator = models.ForeignKey(User, related_name="award_creator",
                                blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    def save(self, *args, **kwargs):
        super(Award, self).save(*args, **kwargs)
        # Reset any progress for this user & badge upon award.
        Progress.objects.filter(user=self.user, badge=self.badge).delete()


class ProgressManager(models.Manager):
    pass


class Progress(models.Model):
    """Record tracking progress toward auto-award of a badge"""
    badge = models.ForeignKey(Badge)
    user = models.ForeignKey(User, related_name="progress_user")
    percent = models.FloatField(default=0)
    counter = models.FloatField(default=0)
    notes = JSONField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    class Meta:
        unique_together = ('badge', 'user')

    get_permissions_for = get_permissions_for

    def save(self, *args, **kwargs):
        """Save the progress record, with before and after signals"""
        super(Progress, self).save(*args, **kwargs)

        # If the percent is over/equal to 1.0, auto-award on save.
        if self.percent >= 100:
            self.badge.award_to(self.user)

    def update_percent(self, current, total=None):
        """Update the percent completion value."""
        if total is None:
            value = current
        else:
            value = (float(current) / float(total)) * 100.0
        self.percent = value
        self.save()

    def increment_by(self, amount):
        # TODO: Do this with an UPDATE counter+amount in DB
        self.counter += amount
        self.save()
        return self

    def decrement_by(self, amount):
        # TODO: Do this with an UPDATE counter-amount in DB
        self.counter -= amount
        self.save()
        return self
