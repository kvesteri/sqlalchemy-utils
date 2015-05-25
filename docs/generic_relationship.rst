Generic relationships
=====================

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
    user = User()
    customer = Customer()

    session.add_all([user, customer])
    session.commit()

    ev = Event()
    ev.object = user

    session.add(ev)
    session.commit()

    # Find the event we just made.
    session.query(Event).filter_by(object=user).first()

    # Find any events that are bound to users.
    session.query(Event).filter(Event.object.is_type(User)).all()


Inheritance
-----------

::

    class Employee(self.Base):
        __tablename__ = 'employee'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(50))
        type = sa.Column(sa.String(20))

        __mapper_args__ = {
            'polymorphic_on': type,
            'polymorphic_identity': 'employee'
        }

    class Manager(Employee):
        __mapper_args__ = {
            'polymorphic_identity': 'manager'
        }

    class Engineer(Employee):
        __mapper_args__ = {
            'polymorphic_identity': 'engineer'
        }

    class Activity(self.Base):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)

        object_type = sa.Column(sa.Unicode(255))
        object_id = sa.Column(sa.Integer, nullable=False)

        object = generic_relationship(object_type, object_id)


Now same as before we can add some objects::

    manager = Manager()

    session.add(manager)
    session.commit()

    activity = Activity()
    activity.object = manager

    session.add(activity)
    session.commit()

    # Find the activity we just made.
    session.query(Event).filter_by(object=manager).first()


We can even test super types::


    session.query(Activity).filter(Event.object.is_type(Employee)).all()


Abstract base classes
---------------------

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


Composite keys
--------------

For some very rare cases you may need to use generic_relationships with composite primary keys. There is a limitation here though: you can only set up generic_relationship for similar composite primary key types. In other words you can't mix generic relationship to both composite keyed objects and single keyed objects.

::

    from sqlalchemy_utils import generic_relationship


    class Customer(Base):
        __tablename__ = 'customer'
        code1 = sa.Column(sa.Integer, primary_key=True)
        code2 = sa.Column(sa.Integer, primary_key=True)


    class Event(Base):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)

        # This is used to discriminate between the linked tables.
        object_type = sa.Column(sa.Unicode(255))

        object_code1 = sa.Column(sa.Integer)

        object_code2 = sa.Column(sa.Integer)

        object = generic_relationship(
            object_type, (object_code1, object_code2)
        )
