from __future__ import unicode_literals
import sqlalchemy as sa
from sqlalchemy_utils import generic_relationship
from tests.generic_relationship import GenericRelationshipTestCase


class TestGenericRelationship(GenericRelationshipTestCase):
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
