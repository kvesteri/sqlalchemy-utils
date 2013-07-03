"""
SQLAlchemy-Utils
----------------

Various utility functions and custom data types for SQLAlchemy.
"""
from setuptools import setup, Command
import subprocess


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        errno = subprocess.call(['py.test'])
        raise SystemExit(errno)


setup(
    name='SQLAlchemy-Utils',
    version='0.14.4',
    url='https://github.com/kvesteri/sqlalchemy-utils',
    license='BSD',
    author='Konsta Vesterinen',
    author_email='konsta@fastmonkeys.com',
    description=(
        'Various utility functions for SQLAlchemy.'
    ),
    long_description=__doc__,
    packages=['sqlalchemy_utils'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    dependency_links=[
        # 5.6 supports python 3.x / pending release
        'git+git://github.com/daviddrysdale/python-phonenumbers.git@python3'
        '#egg=phonenumbers3k-5.6b1',
    ],
    install_requires=[
        'six',
        'SQLAlchemy>=0.8.0',
        'phonenumbers3k==5.6b1',
        'colour>=0.0.3'
    ],
    extras_require={
        'test': [
            'pytest==2.2.3',
            'Pygments>=1.2',
            'Jinja2>=2.3',
            'docutils>=0.10',
            'flexmock>=0.9.7',
        ]
    },
    cmdclass={'test': PyTest},
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
