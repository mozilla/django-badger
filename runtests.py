#!/usr/bin/env python
import os, sys
from django.conf import settings
import nose


settings.configure(
    SITE_ID = 1,
    DEBUG = True,
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner',
    ROOT_URLCONF = 'badger.tests.urls',
    DATABASES = {
        'default': {
            'NAME': 'test-badger.db',
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    SUPPORTED_NONLOCALES = ['media', 'admin'],
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.sites',
        'django.contrib.messages',
        'django_nose',
        'tower',
        'funfactory',
        'badger',
    ],
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'badger.middleware.RecentAwardsMiddleware',
    ),
    TEMPLATE_DIRS = (
        'badger/tests/badger_example/templates',
    ),
    TEMPLATE_LOADERS = (
        'jingo.Loader',
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ),
    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.contrib.auth.context_processors.auth',
        'django.core.context_processors.debug',
        'django.core.context_processors.media',
        'django.core.context_processors.request',
        'session_csrf.context_processor',
        'django.contrib.messages.context_processors.messages',
        'funfactory.context_processors.i18n',
        'funfactory.context_processors.globals',
    ),
    MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage',
    BADGER_TEMPLATE_BASE = 'badger_playdoh',
    LANGUAGE_URL_MAP = {'en-US': 'en_US'}
)


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
