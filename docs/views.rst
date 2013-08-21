.. _chapter-views:

Views
=====

django-badger provides a series of views for:

* listing badges
* showing details for a badge
* creating, editing and deleting badges
* awarding, unawarding, recently awarded list and showing badge award details
* claiming awarded badges
* listing unclaimed badges
* listing all the awarded badges for a user
* listing all the users a badge has been awarded to
* listing all the badges created by a user
* nominating a user for a badge, listing nominations and showing
  nomination details

You can use these views by adding the relevant urls to your Django
project and writing the templates that they use.

The location of the templates is determined by the
``BADGER_TEMPLATE_BASE`` setting. This defaults to ``badger``.

.. Note::

   The view code is in flux, so it's probably best to look at the code
   for implementing your templates.


Adding urls
-----------

There are two urls files. If you want to use the views, you should add
one of them:

``badger/urls_simplified.py``
    Holds url routes for all the views except the "multiplayer
    ones". This assumes that badges will be managed primarily in the
    admin and badges will be awarded by triggers in ``badges.py``
    files.

``badger/urls.py``
    Everything in ``badger/urls_simplified.py`` plus url routes for
    "multiplayer views" allowing users to create awards, nominate
    others for awards and all that.


Views
-----

.. autofunction:: badger.views.home

.. autofunction:: badger.views.badges_list

.. autofunction:: badger.views.detail

.. autofunction:: badger.views.create

.. autofunction:: badger.views.edit

.. autofunction:: badger.views.delete

.. autofunction:: badger.views.award_badge

.. autofunction:: badger.views.awards_list

.. autofunction:: badger.views.award_detail

.. autofunction:: badger.views.award_delete

.. autofunction:: badger.views.claim_deferred_award

.. autofunction:: badger.views.claims_list

.. autofunction:: badger.views.awards_by_user

.. autofunction:: badger.views.awards_by_badge

.. autofunction:: badger.views.badges_by_user

.. autofunction:: badger.views.nomination_detail

.. autofunction:: badger.views.nominate_for
