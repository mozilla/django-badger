API
===

Models
------

.. autoclass:: badger.models.Award
   :members: get_absolute_url, get_upload_meta, bake_obi_image,
             nomination

.. autoclass:: badger.models.Badge
   :members: get_absolute_url, get_upload_meta, clean,
             generate_deferred_awards, get_claim_group,
             delete_claim_group, claim_groups, award_to,
             check_prerequisites, is_awarded_to, progress_for,
             allows_nominate_for, nominate_for, is_nominated_for,
             as_obi_serialization,

.. autoclass:: badger.models.DeferredAward
   :members: get_claim_url, claim, grant_to

.. autoclass:: badger.models.Nomination
   :members: get_absolute_url, is_approved, is_accepted, accept,
             is_rejected, reject_by

.. autoclass:: badger.models.Progress
   :members: update_percent, increment_by, decrement_by


Signals
-------

.. automodule:: badger.signals

   .. autofunction:: badger.signals.badge_will_be_awarded

   .. autofunction:: badger.signals.badge_was_awarded

   .. autofunction:: badger.signals.user_will_be_nominated

   .. autofunction:: badger.signals.user_was_nominated

   .. autofunction:: badger.signals.nomination_will_be_approved

   .. autofunction:: badger.signals.nomination_was_approved

   .. autofunction:: badger.signals.nomination_will_be_accepted

   .. autofunction:: badger.signals.nomination_was_accepted

   .. autofunction:: badger.signals.nomination_will_be_rejected

   .. autofunction:: badger.signals.nomination_was_rejected


Middleware
----------

.. autoclass:: badger.middleware.RecentBadgeAwardsMiddleware


Utility functions
-----------------

.. autofunction:: badger.utils.award_badge

.. autofunction:: badger.utils.get_badge

.. autofunction:: badger.utils.get_progress

.. autofunction:: badger.utils.update_badges
