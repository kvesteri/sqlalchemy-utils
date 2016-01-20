Installation
============

This part of the documentation covers the installation of SQLAlchemy-Utils.

Supported platforms
-------------------

SQLAlchemy-Utils has been tested against the following Python platforms.

- cPython 2.6
- cPython 2.7
- cPython 3.3
- cPython 3.4
- cPython 3.5


Installing an official release
------------------------------

You can install the most recent official SQLAlchemy-Utils version using
pip_::

    pip install sqlalchemy-utils

.. _pip: http://www.pip-installer.org/

Installing the development version
----------------------------------

To install the latest version of SQLAlchemy-Utils, you need first obtain a
copy of the source. You can do that by cloning the git_ repository::

    git clone git://github.com/kvesteri/sqlalchemy-utils.git

Then you can install the source distribution using the ``setup.py``
script::

    cd sqlalchemy-utils
    python setup.py install

.. _git: http://git-scm.org/

Checking the installation
-------------------------

To check that SQLAlchemy-Utils has been properly installed, type ``python``
from your shell. Then at the Python prompt, try to import SQLAlchemy-Utils,
and check the installed version:

.. parsed-literal::

    >>> import sqlalchemy_utils
    >>> sqlalchemy_utils.__version__
    |release|
