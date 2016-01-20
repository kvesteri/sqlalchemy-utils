import pytest
import sqlalchemy as sa

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
def Event(Base):
    class Event(Base):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)

        object_type = sa.Column(sa.Unicode(255), name="objectType")
        object_id = sa.Column(sa.Integer, nullable=False)

        object = generic_relationship(object_type, object_id)
    return Event


@pytest.fixture
def init_models(Building, User, Event):
    pass


class TestGenericRelationship(GenericRelationshipTestCase):
    pass
