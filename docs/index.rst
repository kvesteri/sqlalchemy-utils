.. SQLAlchemy-Utils documentation master file, created by
   sphinx-quickstart on Tue Feb 19 11:16:09 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SQLAlchemy-Utils
================

SQLAlchemy-Utils provides various utility classes and functions for SQLAlchemy.

ScalarList
----------

ScalarList type provides convenient way for saving multiple scalar values in one
column. ScalarList works like list on python side and saves the result as comma-separated list
in the database (custom separators can also be used).

Example ::


    from sqlalchemy_utils import ScalarList


    class User(Base):
        __tablename__ = 'user'
        id = db.Column(db.Integer, autoincrement=True)
        hobbies = db.Column(ScalarList())


    user = User()
    user.hobbies = [u'football', u'ice_hockey']
    session.commit()


You can easily set up integer lists too:

::


    from sqlalchemy_utils import ScalarList


    class Player(Base):
        __tablename__ = 'player'
        id = db.Column(db.Integer, autoincrement=True)
        points = db.Column(ScalarList(int))


    player = Player()
    player.points = [11, 12, 8, 80]
    session.commit()



API Documentation
-----------------

.. module:: sqlalchemy_utils
.. autoclass:: InstrumentedList
    :members:
.. autofunction:: sort_query
.. autofunction:: escape_like

.. include:: ../CHANGES.rst


License
-------

.. include:: ../LICENSE
