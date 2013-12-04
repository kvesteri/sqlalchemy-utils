from __future__ import unicode_literals
import sqlalchemy as sa
from tests import TestCase
from sqlalchemy_utils import batch_fetch, generic_relationship


class TestBatchFetchGenericRelationship(TestCase):
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

            object_type = sa.Column(sa.Unicode(255))
            object_id = sa.Column(sa.Integer, nullable=False)

            object = generic_relationship(object_type, object_id)

        self.Building = Building
        self.User = User
        self.Event = Event

    def test_batch_fetch(self):
        user = self.User()

        self.session.add(user)
        self.session.commit()
        event = self.Event(object=user)
        self.session.add(event)
        self.session.commit()

        events = self.session.query(self.Event).all()
        batch_fetch(events, 'object')
        query_count = self.connection.query_count
        events[0].object

        assert self.connection.query_count == query_count
