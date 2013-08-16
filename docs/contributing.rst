Contributing
============

Installing
----------

To get the source code and all the requirements for django-badger
tests to run, do this::

    $ git clone https://github.com/mozilla/django-badger
    $ mkvirtualenv badger
    $ pip install -r requirements/dev.txt


Running Tests
-------------

django-badger uses `django-nose
<https://github.com/jbalogh/django-nose>`_ which is a Django-centric
test runner that uses `nose
<https://nose.readthedocs.org/en/latest/>`_.

To run the tests, do this::

    $ python manager.py test


Contact us
----------

We hang out on ``#badger`` on irc.mozilla.org.


Pull Requests Welcome!
----------------------

.. TODO

.. vim:set tw=78 ai fo+=n fo-=l ft=rst:
