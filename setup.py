#!/usr/bin/env python
from setuptools import find_packages, setup
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
    url='http://github.com/mozilla/django-badger',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'django>=1.4',
        'PIL',
    ],
    tests_require=[
        'nose',
        'django-nose',
        'pyquery',
        'feedparser',
    ],
    test_suite='manage.nose_collector',
)
