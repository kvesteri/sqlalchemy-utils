"""
SQLAlchemy-Utils
----------------

Various utility functions and custom data types for SQLAlchemy.
"""
from setuptools import setup, find_packages
import sys


PY3 = sys.version_info[0] == 3


extras_require = {
    'test': [
        'pytest==2.2.3',
        'Pygments>=1.2',
        'Jinja2>=2.3',
        'docutils>=0.10',
        'flexmock>=0.9.7',
        'psycopg2>=2.5.1',
        'pytz>=2014.2',
        'python-dateutil>=2.2',
        'pymysql'
    ],
    'anyjson': ['anyjson>=0.3.3'],
    'babel': ['Babel>=1.3'],
    'arrow': ['arrow>=0.3.4'],
    'intervals': ['intervals>=0.2.4'],
    'phone': ['phonenumbers>=5.9.2'],
    'password': ['passlib >= 1.6, < 2.0'],
    'color': ['colour>=0.0.4'],
    'ipaddress': ['ipaddr'] if not PY3 else [],
    'timezone': ['python-dateutil'],
    'url': ['furl >= 0.3.5'] if not PY3 else []
}


# Add all optional dependencies to testing requirements.
for name, requirements in extras_require.items():
    if name != 'test':
        extras_require['test'] += requirements


setup(
    name='SQLAlchemy-Utils',
    version='0.26.13',
    url='https://github.com/kvesteri/sqlalchemy-utils',
    license='BSD',
    author='Konsta Vesterinen, Ryan Leckey, Janne Vanhala, Vesa Uimonen',
    author_email='konsta@fastmonkeys.com',
    description=(
        'Various utility functions for SQLAlchemy.'
    ),
    long_description=__doc__,
    packages=find_packages('.', exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    dependency_links=[
        # 5.6b1 only supports python 3.x / pending release
        'git+git://github.com/daviddrysdale/python-phonenumbers.git@python3'
        '#egg=phonenumbers3k-5.6b1',
    ],
    install_requires=[
        'six',
        'SQLAlchemy>=0.9.3',
        'total_ordering>=0.1'
        if sys.version_info[0] == 2 and sys.version_info[1] < 7 else '',
        'ordereddict>=1.1'
        if sys.version_info[0] == 2 and sys.version_info[1] < 7 else '',
    ],
    extras_require=extras_require,
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
