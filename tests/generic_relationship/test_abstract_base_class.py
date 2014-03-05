from __future__ import unicode_literals
import sqlalchemy as sa
from sqlalchemy_utils import generic_relationship
from sqlalchemy.ext.declarative import declared_attr
from tests.generic_relationship import GenericRelationshipTestCase


class TestGenericRelationshipWithAbstractBase(GenericRelationshipTestCase):
    def create_models(self):
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

        self.Building = Building
        self.User = User
        self.Event = Event
