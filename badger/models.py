from django.db import models
from django.contrib.auth.models import User, AnonymousUser

from django.template.defaultfilters import slugify

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse


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


class BadgerException(Exception):
    """General Badger model exception"""


class BadgeManager(models.Manager):
    """Manager for Badge model objects"""


class BadgeException(BadgerException):
    """Badge model exception"""


class BadgeAwardNotAllowedException(BadgeException):
    """Attempt to award a badge not allowed."""


class Badge(models.Model):
    """Representation of a badge"""
    objects = BadgeManager()

    title = models.CharField(max_length=255, blank=False, unique=True)
    slug = models.SlugField(blank=False, unique=True)
    description = models.TextField(blank=True)
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
        award = Award(user=awardee, badge=self, creator=awarder,
                nomination=nomination)
        award.save()
        return award

    def is_awarded_to(self, user):
        """Has this badge been awarded to the user?"""
        return Award.objects.filter(user=user, badge=self).count() > 0

    def nominate_for(self, nominator, nominee):
        """Nominate a nominee for this badge on the nominator's behalf"""
        nomination = Nomination(badge=self, creator=nominator, nominee=nominee)
        nomination.save()
        return nomination

    def is_nominated_for(self, user):
        return Nomination.objects.filter(nominee=user, badge=self).count() > 0


class NominationManager(models.Manager):
    pass


class NominationException(BadgerException):
    """Nomination model exception"""


class NominationApproveNotAllowedException(NominationException):
    """Attempt to approve a nomination was disallowed"""


class NominationAcceptNotAllowedException(NominationException):
    """Attempt to accept a nomination was disallowed"""


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
        self.save()
        self._award_if_ready()

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
        self.save()
        self._award_if_ready()

    def is_accepted(self):
        """Has this nomination been accepted?"""
        return self.accepted

    def _award_if_ready(self):
        """If approved and accepted, award the badge to nominee on behalf of
        approver."""
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
