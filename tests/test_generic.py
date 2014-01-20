from __future__ import unicode_literals
import sqlalchemy as sa
from tests import TestCase
from sqlalchemy_utils import generic_relationship


class TestGenericForiegnKey(TestCase):

    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)

        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

        class Event(self.Base):
            __tablename__ = 'event'
            id = sa.Column(sa.Integer, primary_key=True)

            object_type = sa.Column(sa.Unicode(255), name="objectType")
            object_id = sa.Column(sa.Integer, nullable=False)

            object = generic_relationship(object_type, object_id)

        self.Building = Building
        self.User = User
        self.Event = Event

    def test_set_as_none(self):
        event = self.Event()
        event.object = None

    def test_set_manual_and_get(self):
        user = self.User()

        self.session.add(user)
        self.session.commit()

        event = self.Event()
        event.object_id = user.id
        event.object_type = type(user).__tablename__

        assert event.object is None

        self.session.add(event)
        self.session.commit()

        assert event.object == user

    def test_set_and_get(self):
        user = self.User()

        self.session.add(user)
        self.session.commit()

        event = self.Event(object=user)

        assert event.object_id == user.id
        assert event.object_type == type(user).__tablename__

        self.session.add(event)
        self.session.commit()

        assert event.object == user

    def test_compare_instance(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event = self.Event(object=user1)

        self.session.add(event)
        self.session.commit()

        assert event.object == user1
        assert event.object != user2

    def test_compare_query(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event = self.Event(object=user1)

        self.session.add(event)
        self.session.commit()

        q = self.session.query(self.Event)
        assert q.filter_by(object=user1).first() is not None
        assert q.filter_by(object=user2).first() is None
        assert q.filter(self.Event.object == user2).first() is None

    def test_compare_not_query(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event = self.Event(object=user1)

        self.session.add(event)
        self.session.commit()

        q = self.session.query(self.Event)
        assert q.filter(self.Event.object != user2).first() is not None

    def test_compare_type(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event1 = self.Event(object=user1)
        event2 = self.Event(object=user2)

        self.session.add_all([event1, event2])
        self.session.commit()

        statement = self.Event.object.is_type(self.User)
        q = self.session.query(self.Event).filter(statement)
        assert q.first() is not None
