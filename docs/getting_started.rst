.. _chapter-getting-started:

Getting Started
===============

Setup
-----

1. Install django-badger. Currently there's no released version, so
   you need to install it from git::

       pip install -e https://github.com/mozilla/django-badger/zipball/master#egg=django-badger

2. (Optional) Install django-notification.
3. Configure django-badger. See :ref:`chapter-getting-started-conf`.
4. Add settings to your Django settings file. See the Configuration
   section.
5. (Optional) Add ``badges.py`` files to your Django apps. FIXME -
   need docs for this.
6. Set up string extraction so that django-badger strings are
   translated.

See  `badg.us <https://github.com/mozilla/badg.us>`_ for an example
site setup.


.. _chapter-getting-started-conf:

Configuration
-------------

BADGER_TEMPLATE_BASE
    String. The prefix for template files. Default is "badger".

    For example, if the value is "foo", then the django-badger home
    view renders the template "foo/home.html".

ALLOW_ADD_BY_ANYONE
    Boolean. Master switch for wide-open badge creation by all
    users. This is also known as "multiplayer mode".

BADGE_PAGE_SIZE
    Integer. Page size for badge listings. Default is 50.

MAX_RECENT
    Integer. Number of items shown on home page recent
    sections. Default is 15.


See  `badg.us <https://github.com/lmorchard/badg.us>`_ for an example
site setup

See ``badger_example/badges.py`` in the source code for another
example.


Setting up views and/or using the API
-------------------------------------

See :ref:`chapter-views` for documentation on the views that come with
django-badger and how to use them.

See :ref:`chapter-api` for documentation on the django-badger API.

.. vim:set tw=78 ai fo+=n fo-=l ft=rst:
