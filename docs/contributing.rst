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


You can also run the tests with `tox <http://tox.readthedocs.org/en/latest/>`_
which will run the tests in Python 2.6 and 2.7 for Django 1.4 and 1.5. to do
that, do this::

    $ tox


Contact us
----------

We hang out on ``#badger`` on irc.mozilla.org.


Pull Requests Welcome!
----------------------

.. TODO

.. vim:set tw=78 ai fo+=n fo-=l ft=rst:
