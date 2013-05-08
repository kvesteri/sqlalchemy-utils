.. SQLAlchemy-Utils documentation master file, created by
   sphinx-quickstart on Tue Feb 19 11:16:09 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SQLAlchemy-Utils
================

SQLAlchemy-Utils provides custom data types and various utility functions for SQLAlchemy.

Using automatic data coercion
-----------------------------

SQLAlchemy-Utils provides various new data types for SQLAlchemy and in order to gain full
advantage of these datatypes you should use coercion_listener. Setting up the listener is easy:

::

    import sqlalchemy as sa
    from sqlalchemy_utils import coercion_listener


    sa.event.listen(sa.orm.mapper, 'mapper_configured', coercion_listener)


The listener automatically detects SQLAlchemy-Utils compatible data types and coerces all attributes
using these types to appropriate objects.


Example
::
    from colour import Color
    from sqlalchemy_utils import ColorType


    class Document(Base):
        __tablename__ = 'player'
        id = db.Column(db.Integer, autoincrement=True)
        name = db.Column(db.Unicode(50))
        background_color = db.Column(ColorType)


    document = Document()
    document.background_color = 'F5F5F5'
    document.background_color  # Color object
    session.commit()


ScalarListType
--------------

ScalarListType type provides convenient way for saving multiple scalar values in one
column. ScalarListType works like list on python side and saves the result as comma-separated list
in the database (custom separators can also be used).

Example ::


    from sqlalchemy_utils import ScalarListType


    class User(Base):
        __tablename__ = 'user'
        id = db.Column(db.Integer, autoincrement=True)
        hobbies = db.Column(ScalarListType())


    user = User()
    user.hobbies = [u'football', u'ice_hockey']
    session.commit()


You can easily set up integer lists too:

::


    from sqlalchemy_utils import ScalarListType


    class Player(Base):
        __tablename__ = 'player'
        id = db.Column(db.Integer, autoincrement=True)
        points = db.Column(ScalarListType(int))


    player = Player()
    player.points = [11, 12, 8, 80]
    session.commit()


ColorType
---------

ColorType provides a way for saving Color (from colour package) objects into database.
ColorType saves Color objects as strings on the way in and converts them back to objects when querying the database.

::


    from colour import Color
    from sqlalchemy_utils import ColorType


    class Document(Base):
        __tablename__ = 'player'
        id = db.Column(db.Integer, autoincrement=True)
        name = db.Column(db.Unicode(50))
        background_color = db.Column(ColorType)


    document = Document()
    document.background_color = Color('#F5F5F5')
    session.commit()


Querying the database returns Color objects:

::

    document = session.query(Document).first()

    document.background_color.hex
    # '#f5f5f5'


For more information about colour package and Color object, see https://github.com/vaab/colour


NumberRangeType
---------------

NumberRangeType provides way for saving range of numbers into database.

Example ::


    from sqlalchemy_utils import NumberRangeType, NumberRange


    class Event(Base):
        __tablename__ = 'user'
        id = db.Column(db.Integer, autoincrement=True)
        name = db.Column(db.Unicode(255))
        estimated_number_of_persons = db.Column(NumberRangeType)


    party = Event(name=u'party')

    # we estimate the party to contain minium of 10 persons and at max
    # 100 persons
    party.estimated_number_of_persons = NumberRange(10, 100)

    print party.estimated_number_of_persons
    # '10-100'


NumberRange supports some arithmetic operators:
::


    meeting = Event(name=u'meeting')

    meeting.estimated_number_of_persons = NumberRange(20, 40)

    total = (
        meeting.estimated_number_of_persons +
        party.estimated_number_of_persons
    )
    print total
    # '30-140'


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
