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


Using generic_relationship with abstract base classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Generic relationships also allows using string arguments. When using generic_relationship with abstract base classes you need to set up the relationship using declared_attr decorator and string arguments.


::


    class Building(self.Base):
        __tablename__ = 'building'
        id = sa.Column(sa.Integer, primary_key=True)

    class User(self.Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)

    class EventBase(self.Base):
        __abstract__ = True

        object_type = sa.Column(sa.Unicode(255))
        object_id = sa.Column(sa.Integer, nullable=False)

        @declared_attr
        def object(cls):
            return generic_relationship('object_type', 'object_id')

    class Event(EventBase):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)
