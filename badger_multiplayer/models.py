from django.db import models
from django.db.models import signals
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json
from django.contrib.auth.models import User, AnonymousUser

from django.template.defaultfilters import slugify

try:
    from commons.urlresolvers import reverse
except ImportError, e:
    from django.core.urlresolvers import reverse

import badger.models
from badger.models import (Award, BadgerException,
                           BadgeAlreadyAwardedException,
                           get_permissions_for)

from .signals import (nomination_will_be_approved, nomination_was_approved,
                      nomination_will_be_accepted, nomination_was_accepted,
                      user_will_be_nominated, user_was_nominated, )


class Badge(badger.models.Badge):
    """Enhanced Badge model with multiplayer features"""
    
    class Meta:
        proxy = True

    get_permissions_for = get_permissions_for

    def allows_nominate_for(self, user):
        """Is nominate_for() allowed for this user?"""
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
        return Nomination.objects.create(badge=self, creator=nominator,
                                         nominee=nominee)

    def is_nominated_for(self, user):
        return Nomination.objects.filter(nominee=user, badge=self).count() > 0


class Award(badger.models.Award):
    """Enhanced Award model with multiplayer features"""

    class Meta:
        proxy = True

    @property
    def badge(self):
        """Property that wraps the related badge in a multiplayer upgrade"""
        new_inst = Badge()
        new_inst.__dict__ = super(Award, self).badge.__dict__
        return new_inst


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
            blank=True, null=True)
    approver = models.ForeignKey(User, related_name="nomination_approver",
            blank=True, null=True)
    award = models.ForeignKey(Award, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, blank=False)
    modified = models.DateTimeField(auto_now=True, blank=False)

    get_permissions_for = get_permissions_for

    def __unicode__(self):
        return u'Nomination for %s to %s by %s' % (self.badge, self.nominee,
                                                   self.creator)

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

        if self.is_approved() and self.is_accepted():
            # HACK: Convert the original-flavor Award into a multiplayer Award
            # before assigning to self.
            real_award = self.badge.award_to(self.nominee, self.approver)
            award = Award()
            award.__dict__ = real_award.__dict__
            self.award = award
            # This was the original code, which caused errors:
            # self.award = self.badge.award_to(self.nominee, self.approver)

        super(Nomination, self).save(*args, **kwargs)

        if is_new:
            user_was_nominated.send(sender=self.__class__,
                                    nomination=self)

    def allows_detail_by(self, user):
        if (user.is_staff or 
               user.is_superuser or
               user == self.badge.creator or
               user == self.nominee or
               user == self.creator ):
            return True

        # TODO: List of delegates empowered by badge creator to approve nominations

        return False

    def allows_approve_by(self, user):
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
        nomination_was_accepted.send(sender=self.__class__,
                                     nomination=self)
        return self

    def is_accepted(self):
        """Has this nomination been accepted?"""
        return self.accepted
