=============
django-badger
=============

.. image:: https://secure.travis-ci.org/lmorchard/django-badger.png?branch=master
   :target: http://travis-ci.org/lmorchard/django-badger

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
- Views and models that enable users to create their own badges and nominate
  each other for awards.
- Meta-badges, for which an award is automatically issued when a complete set
  of prerequisite badge awards have been collected.
- Progress tracking, for which an award is issued when a user metric reaches
  100% of some goal, or in response to some other custom logic.
- Activity streams of badge awards.

If you want to federate or share badges, you should check out
the `Mozilla Open Badges <https://github.com/mozilla/openbadges>`_ project.

Installation
------------

- TBD, see `badg.us <https://github.com/lmorchard/badg.us>`_ for an example
  site setup
- ``pip install git://github.com/lmorchard/django-badger.git#egg=django-badger``

Settings
--------

- TBD, see `badg.us <https://github.com/lmorchard/badg.us>`_ for an example
  site setup
- TBD, see ``badger/tests/badger_example/badges.py`` for an example.


Templates
---------

There are two sets of templates in the templates folder.  The templates
found in ``badger_playdoh`` are intended for use with Playdoh sites, while
those found in ``badger_vanilla`` are meant for plain Django sites.

You'll need to make a copy of one of these folders into a directory named
``templates/badger`` at the top level of your project. Then, you can customize
the templates as necessary for your site.

Creating badges
---------------

- TBD, see ``badger/tests/badger_example/badges.py`` for an example.


Awarding badges
---------------

- TBD, see ``badger/tests/badger_example/badges.py`` for an example.


Testing
-------

- TBD, see `badg.us <https://github.com/lmorchard/badg.us>`_ for an example
  site setup

.. vim:set tw=78 ai fo+=n fo-=l ft=rst:
