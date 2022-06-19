import pytest
import sqlalchemy as sa

from sqlalchemy_utils import generic_relationship


@pytest.fixture
def Employee(Base):
    class Employee(Base):
        __tablename__ = 'employee'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(50))
        type = sa.Column(sa.String(20))

        __mapper_args__ = {
            'polymorphic_on': type,
            'polymorphic_identity': 'employee'
        }
    return Employee


@pytest.fixture
def Manager(Employee):
    class Manager(Employee):
        __mapper_args__ = {
            'polymorphic_identity': 'manager'
        }
    return Manager


@pytest.fixture
def Engineer(Employee):
    class Engineer(Employee):
        __mapper_args__ = {
            'polymorphic_identity': 'engineer'
        }
    return Engineer


@pytest.fixture
def Event(Base):
    class Event(Base):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)

        object_type = sa.Column(sa.Unicode(255))
        object_id = sa.Column(sa.Integer, nullable=False)

        object = generic_relationship(object_type, object_id)
    return Event


@pytest.fixture
def init_models(Employee, Manager, Engineer, Event):
    pass


class TestGenericRelationship:

    def test_set_as_none(self, Event):
        event = Event()
        event.object = None
        assert event.object is None

    def test_set_manual_and_get(self, session, Manager, Event):
        manager = Manager()

        session.add(manager)
        session.commit()

        event = Event()
        event.object_id = manager.id
        event.object_type = type(manager).__name__

        assert event.object is None

        session.add(event)
        session.commit()

        assert event.object == manager

    def test_set_and_get(self, session, Manager, Event):
        manager = Manager()

        session.add(manager)
        session.commit()

        event = Event(object=manager)

        assert event.object_id == manager.id
        assert event.object_type == type(manager).__name__

        session.add(event)
        session.commit()

        assert event.object == manager

    def test_compare_instance(self, session, Manager, Event):
        manager1 = Manager()
        manager2 = Manager()

        session.add_all([manager1, manager2])
        session.commit()

        event = Event(object=manager1)

        session.add(event)
        session.commit()

        assert event.object == manager1
        assert event.object != manager2

    def test_compare_query(self, session, Manager, Event):
        manager1 = Manager()
        manager2 = Manager()

        session.add_all([manager1, manager2])
        session.commit()

        event = Event(object=manager1)

        session.add(event)
        session.commit()

        q = session.query(Event)
        assert q.filter_by(object=manager1).first() is not None
        assert q.filter_by(object=manager2).first() is None
        assert q.filter(Event.object == manager2).first() is None

    def test_compare_not_query(self, session, Manager, Event):
        manager1 = Manager()
        manager2 = Manager()

        session.add_all([manager1, manager2])
        session.commit()

        event = Event(object=manager1)

        session.add(event)
        session.commit()

        q = session.query(Event)
        assert q.filter(Event.object != manager2).first() is not None

    def test_compare_type(self, session, Manager, Event):
        manager1 = Manager()
        manager2 = Manager()

        session.add_all([manager1, manager2])
        session.commit()

        event1 = Event(object=manager1)
        event2 = Event(object=manager2)

        session.add_all([event1, event2])
        session.commit()

        statement = Event.object.is_type(Manager)
        q = session.query(Event).filter(statement)
        assert q.first() is not None

    def test_compare_super_type(self, session, Manager, Event, Employee):
        manager1 = Manager()
        manager2 = Manager()

        session.add_all([manager1, manager2])
        session.commit()

        event1 = Event(object=manager1)
        event2 = Event(object=manager2)

        session.add_all([event1, event2])
        session.commit()

        statement = Event.object.is_type(Employee)
        q = session.query(Event).filter(statement)
        assert q.first() is not None
