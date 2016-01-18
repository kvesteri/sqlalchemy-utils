import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy_utils import generic_relationship

from . import GenericRelationshipTestCase


@pytest.fixture
def Building(Base):
    class Building(Base):
        __tablename__ = 'building'
        id = sa.Column(sa.Integer, primary_key=True)
    return Building


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
    return User


@pytest.fixture
def EventBase(Base):
    class EventBase(Base):
        __abstract__ = True

        object_type = sa.Column(sa.Unicode(255))
        object_id = sa.Column(sa.Integer, nullable=False)

        @declared_attr
        def object(cls):
            return generic_relationship('object_type', 'object_id')
    return EventBase


@pytest.fixture
def Event(EventBase):
    class Event(EventBase):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)
    return Event


@pytest.fixture
def init_models(Building, User, Event):
    pass


class TestGenericRelationshipWithAbstractBase(GenericRelationshipTestCase):
    pass
