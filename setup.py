#!/usr/bin/env python
from setuptools import setup
try:
    import multiprocessing
except ImportError:
    pass


setup(
    name='django-badger',
    version='0.0.1',
    description='Django app for managing and awarding badgers',
    long_description=open('README.rst').read(),
    author='Leslie Michael Orchard',
    author_email='me@lmorchard.com',
    url='http://github.com/lmorchard/django-badger',
    license='BSD',
    packages=['badger', 'badger.templatetags',  'badger.management', 'badger.management.commands', 'badger.migrations'],
    package_data={'badger': ['fixtures/*', 'templates/badger_playdoh/*.html', 'templates/badger_playdoh/includes/*.html', 'templates/badger_vanilla/*.html', 'templates/badger_vanilla/includes/*.html']},
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        # I don't know what exactly this means, but why not?
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'django>=1.2',
        'PIL',
    ],
    tests_require=[
        'django-setuptest',
        'funfactory',
        'tower',
        'django-session-csrf',
        'jinja2',
        'jingo',
        'nose',
        'django-nose',
        'pyquery',
        'feedparser',
        'django-runtests',
    ],
    #test_suite='runtests.collector',
    #test_suite='nose.collector',
    test_suite='runtests.runtests',
)
