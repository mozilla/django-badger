#!/usr/bin/env python
import os, sys
from django.conf import settings
import nose

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

def runtests():
    from django.core.management import call_command
    call_command('test', 'badger.tests.test_middleware',
                         'badger.tests.test_models',
                         'badger.tests.test_feeds',
                         # TODO: Get views tests passing in this context, someday.
                         #'badger.tests.test_views',
                         'badger.tests.test_badges_py')
    return []


def collector():
    return nose.collector()
