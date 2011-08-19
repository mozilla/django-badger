=============
django-badger
=============

Badger is a family of Django apps intended to help introduce badges into your
project, to track and award achievements by your users. This can be used to
help encourage certain behaviors, recognize skills, or just generally
celebrate members of your community.

For more about the thinking behind this project, check out this essay:
`Why does Mozilla need a Badger?  <http://decafbad.com/2010/07/badger-article/>`_

The ``django-badger`` package is the core Badger app. It offers (or plans to
offer) the following:

- Basic badges, managed by the site owner in code and via Django admin.
- Badge awards, triggered in response to signal-based events with code
  collected in per-app ``badges.py`` modules.
- Meta-badges, for which an award is automatically issued when a complete set
  of prerequisite badge awards have been collected.
- Progress tracking, for which an award is issued when a user metric reaches
  100% of some goal, or in response to some other custom logic.
- Activity streams of badge awards.


Installation
------------

- TBD, see `badger2 <https://github.com/lmorchard/badger2>`_ for an example
  site setup
- ``pip install git://github.com/lmorchard/django-badger.git#egg=django-badger``

Settings
--------

- TBD, see `badger2 <https://github.com/lmorchard/badger2>`_ for an example
  site setup
- TBD, see ``badger/tests/badger_example/badges.py`` for an example.


Creating badges
---------------

- TBD, see ``badger/tests/badger_example/badges.py`` for an example.


Awarding badges
---------------

- TBD, see ``badger/tests/badger_example/badges.py`` for an example.


Testing
-------

- TBD, see `badger2 <https://github.com/lmorchard/badger2>`_ for an example
  site setup


Other Badger apps
-----------------

Here are other apps in the Badger family, either in progress or proposed:

`django-badger-multiplayer <https://github.com/lmorchard/django-badger-multiplayer>`_
    Badges for and by everyone. Augments ``django-badger`` with features to
    make badge creation, nomination, and awarding a multiplayer game.

`django-badger-api <https://github.com/lmorchard/django-badger-api>`_
    Augments ``django-badger`` with a REST API and OAuth so external scripts
    and bots can issue awards and nominations in response to events monitored
    in custom ways. Also, opens the way for things like mobile apps, etc.

`django-badger-federation <https://github.com/lmorchard/django-badger-federation>`_
    Builds on ``django-badger-api`` and Activity Streams with facilities to
    make badging a distributed feature. Your network of sites can be badge
    issuers and badge collection hubs, and you can allow sites outside your
    network to participate.

.. vim:set tw=78 ai fo+=n fo-=l ft=rst:
