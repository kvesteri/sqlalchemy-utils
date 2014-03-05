from __future__ import unicode_literals
import six
import sqlalchemy as sa
from sqlalchemy_utils import generic_relationship
from tests.generic_relationship import GenericRelationshipTestCase


class TestGenericRelationship(GenericRelationshipTestCase):
    index = 1

    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            code = sa.Column(sa.Integer, primary_key=True)

            def __init__(obj_self):
                self.index += 1
                obj_self.id = self.index
                obj_self.code = self.index

        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            code = sa.Column(sa.Integer, primary_key=True)

            def __init__(obj_self):
                self.index += 1
                obj_self.id = self.index
                obj_self.code = self.index

        class Event(self.Base):
            __tablename__ = 'event'
            id = sa.Column(sa.Integer, primary_key=True)

            object_type = sa.Column(sa.Unicode(255))
            object_id = sa.Column(sa.Integer, nullable=False)
            object_code = sa.Column(sa.Integer, nullable=False)

            object = generic_relationship(
                object_type, (object_id, object_code)
            )

        self.Building = Building
        self.User = User
        self.Event = Event

    def test_set_manual_and_get(self):
        user = self.User()

        self.session.add(user)
        self.session.commit()

        event = self.Event()
        event.object_id = user.id
        event.object_type = six.text_type(type(user).__name__)
        event.object_code = user.code

        assert event.object is None

        self.session.add(event)
        self.session.commit()

        assert event.object == user
