SQLAlchemy-Utils
================

.. contents::


SQLAlchemy-Utils provides custom data types and various utility functions for SQLAlchemy.

Using automatic data coercion
=============================

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
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, autoincrement=True)
        name = sa.Column(sa.Unicode(50))
        background_color = sa.Column(ColorType)


    document = Document()
    document.background_color = 'F5F5F5'
    document.background_color  # Color object
    session.commit()



Data types
==========

SQLAlchemy-Utils provides various new data types for SQLAlchemy.

.. module:: sqlalchemy_utils.types


ArrowType
^^^^^^^^^

.. module:: sqlalchemy_utils.types.arrow

.. autoclass:: ArrowType

ChoiceType
^^^^^^^^^^

.. module:: sqlalchemy_utils.types.choice

.. autoclass:: ChoiceType


ColorType
^^^^^^^^^

.. module:: sqlalchemy_utils.types.color

.. autoclass:: ColorType


JSONType
^^^^^^^^

.. module:: sqlalchemy_utils.types.json

.. autoclass:: JSONType


LocaleType
^^^^^^^^^^


.. module:: sqlalchemy_utils.types.locale

.. autoclass:: LocaleType


NumberRangeType
^^^^^^^^^^^^^^^

.. module:: sqlalchemy_utils.types.number_range

.. autoclass:: NumberRangeType


PasswordType
^^^^^^^^^^^^

.. module:: sqlalchemy_utils.types.password

.. autoclass:: PasswordType


PhoneNumberType
^^^^^^^^^^^^^^^

.. module:: sqlalchemy_utils.types.phone_number

.. autoclass:: PhoneNumberType


ScalarListType
^^^^^^^^^^^^^^

.. module:: sqlalchemy_utils.types.scalar_list

.. autoclass:: ScalarListType


TimezoneType
^^^^^^^^^^^^


.. module:: sqlalchemy_utils.types.timezone

.. autoclass:: TimezoneType


URLType
^^^^^^^

.. module:: sqlalchemy_utils.types.url

.. autoclass:: URLType


UUIDType
^^^^^^^^


.. module:: sqlalchemy_utils.types.uuid

.. autoclass:: UUIDType



Aggregated attributes
=====================

.. automodule:: sqlalchemy_utils.aggregates

.. autofunction:: aggregated_attr



The generates decorator
=======================

.. module:: sqlalchemy_utils.decorators

.. autofunction:: generates


Generic Relationship
====================

Generic relationship is a form of relationship that supports creating a 1 to many relationship to any target model.

::

    from sqlalchemy_utils import generic_relationship

    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)

    class Customer(Base):
        __tablename__ = 'customer'
        id = sa.Column(sa.Integer, primary_key=True)

    class Event(Base):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)

        # This is used to discriminate between the linked tables.
        object_type = sa.Column(sa.Unicode(255))

        # This is used to point to the primary key of the linked row.
        object_id = sa.Column(sa.Integer)

        object = generic_relationship(object_type, object_id)


    # Some general usage to attach an event to a user.
    us_1 = User()
    cu_1 = Customer()

    session.add_all([us_1, cu_1])
    session.commit()

    ev = Event()
    ev.object = us_1

    session.add(ev)
    session.commit()

    # Find the event we just made.
    session.query(Event).filter_by(object=us_1).first()

    # Find any events that are bound to users.
    session.query(Event).filter(Event.object.is_type(User)).all()

.. _colour: https://github.com/vaab/colour


Utility functions
=================

.. module:: sqlalchemy_utils.functions


declarative_base
^^^^^^^^^^^^^^^^

.. autofunction:: declarative_base


escape_like
^^^^^^^^^^^

.. autofunction:: escape_like


has_changes
^^^^^^^^^^^

.. autofunction:: has_changes


identity
^^^^^^^^

.. autofunction:: identity


is_indexed_foreign_key
^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: is_indexed_foreign_key


naturally_equivalent
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: naturally_equivalent

non_indexed_foreign_keys
^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: non_indexed_foreign_keys


sort_query
^^^^^^^^^^

.. autofunction:: sort_query


License
=======

.. include:: ../LICENSE
