"""
SQLAlchemy-Utils
----------------

Various utility functions and custom data types for SQLAlchemy.
"""
import os
import re

from setuptools import find_packages, setup

HERE = os.path.dirname(os.path.abspath(__file__))


def get_version():
    filename = os.path.join(HERE, 'sqlalchemy_utils', '__init__.py')
    with open(filename) as f:
        contents = f.read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


extras_require = {
    'test': [
        'pytest>=2.7.1',
        'Pygments>=1.2',
        'Jinja2>=2.3',
        'docutils>=0.10',
        'flexmock>=0.9.7',
        'psycopg2>=2.5.1',
        'psycopg2cffi>=2.8.1',
        'pg8000>=1.12.4',
        'pytz>=2014.2',
        'python-dateutil>=2.6',
        'backports.zoneinfo;python_version<"3.9"',
        'pymysql',
        'flake8>=2.4.0',
        'isort>=4.2.2',
        'pyodbc',
    ],
    'babel': ['Babel>=1.3'],
    'arrow': ['arrow>=0.3.4'],
    'pendulum': ['pendulum>=2.0.5'],
    'intervals': ['intervals>=0.7.1'],
    'phone': ['phonenumbers>=5.9.2'],
    'password': ['passlib >= 1.6, < 2.0'],
    'color': ['colour>=0.0.4'],
    'timezone': ['python-dateutil'],
    'url': ['furl >= 0.4.1'],
    'encrypted': ['cryptography>=0.6']
}


# Add all optional dependencies to testing requirements.
test_all = []
for requirements in extras_require.values():
    test_all += requirements
extras_require['test_all'] = sorted(test_all)


setup(
    name='SQLAlchemy-Utils',
    version=get_version(),
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
    install_requires=[
        'SQLAlchemy>=1.3',
        "importlib_metadata ; python_version<'3.8'",
    ],
    extras_require=extras_require,
    python_requires='~=3.6',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
