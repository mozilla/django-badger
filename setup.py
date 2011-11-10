from setuptools import setup


setup(
    name='django-badger',
    version='0.0.1',
    description='Django app for managing and awarding badgers',
    long_description=open('README.rst').read(),
    author='Leslie Michael Orchard',
    author_email='me@lmorchard.com',
    url='http://github.com/lmorchard/django-badger',
    license='BSD',
    packages=['badger', 'badger.management.commands', 'badger.migrations'],
    package_data={'badger': ['fixtures/*', 'templates/badger/*.html', 'templates/badger/includes/*.html']},
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
    ]
)
