from __future__ import unicode_literals
import six
import sqlalchemy as sa
from sqlalchemy_utils import generic_relationship
from tests import TestCase


class TestGenericRelationship(TestCase):
    def create_models(self):
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

        class Event(self.Base):
            __tablename__ = 'event'
            id = sa.Column(sa.Integer, primary_key=True)

            object_type = sa.Column(sa.Unicode(255))
            object_id = sa.Column(sa.Integer, nullable=False)

            object = generic_relationship(object_type, object_id)

        self.Employee = Employee
        self.Manager = Manager
        self.Engineer = Engineer
        self.Event = Event

    def test_set_as_none(self):
        event = self.Event()
        event.object = None
        assert event.object is None

    def test_set_manual_and_get(self):
        manager = self.Manager()

        self.session.add(manager)
        self.session.commit()

        event = self.Event()
        event.object_id = manager.id
        event.object_type = six.text_type(type(manager).__name__)

        assert event.object is None

        self.session.add(event)
        self.session.commit()

        assert event.object == manager

    def test_set_and_get(self):
        manager = self.Manager()

        self.session.add(manager)
        self.session.commit()

        event = self.Event(object=manager)

        assert event.object_id == manager.id
        assert event.object_type == type(manager).__name__

        self.session.add(event)
        self.session.commit()

        assert event.object == manager

    def test_compare_instance(self):
        manager1 = self.Manager()
        manager2 = self.Manager()

        self.session.add_all([manager1, manager2])
        self.session.commit()

        event = self.Event(object=manager1)

        self.session.add(event)
        self.session.commit()

        assert event.object == manager1
        assert event.object != manager2

    def test_compare_query(self):
        manager1 = self.Manager()
        manager2 = self.Manager()

        self.session.add_all([manager1, manager2])
        self.session.commit()

        event = self.Event(object=manager1)

        self.session.add(event)
        self.session.commit()

        q = self.session.query(self.Event)
        assert q.filter_by(object=manager1).first() is not None
        assert q.filter_by(object=manager2).first() is None
        assert q.filter(self.Event.object == manager2).first() is None

    def test_compare_not_query(self):
        manager1 = self.Manager()
        manager2 = self.Manager()

        self.session.add_all([manager1, manager2])
        self.session.commit()

        event = self.Event(object=manager1)

        self.session.add(event)
        self.session.commit()

        q = self.session.query(self.Event)
        assert q.filter(self.Event.object != manager2).first() is not None

    def test_compare_type(self):
        manager1 = self.Manager()
        manager2 = self.Manager()

        self.session.add_all([manager1, manager2])
        self.session.commit()

        event1 = self.Event(object=manager1)
        event2 = self.Event(object=manager2)

        self.session.add_all([event1, event2])
        self.session.commit()

        statement = self.Event.object.is_type(self.Manager)
        q = self.session.query(self.Event).filter(statement)
        assert q.first() is not None

    def test_compare_super_type(self):
        manager1 = self.Manager()
        manager2 = self.Manager()

        self.session.add_all([manager1, manager2])
        self.session.commit()

        event1 = self.Event(object=manager1)
        event2 = self.Event(object=manager2)

        self.session.add_all([event1, event2])
        self.session.commit()

        statement = self.Event.object.is_type(self.Employee)
        q = self.session.query(self.Event).filter(statement)
        assert q.first() is not None
