import pytest
import sqlalchemy as sa

from sqlalchemy_utils import generic_relationship

from ..generic_relationship import GenericRelationshipTestCase


@pytest.fixture
def incrementor():
    class Incrementor:
        value = 1
    return Incrementor()


@pytest.fixture
def Building(Base, incrementor):
    class Building(Base):
        __tablename__ = 'building'
        id = sa.Column(sa.Integer, primary_key=True)
        code = sa.Column(sa.Integer, primary_key=True)

        def __init__(self):
            incrementor.value += 1
            self.id = incrementor.value
            self.code = incrementor.value
    return Building


@pytest.fixture
def User(Base, incrementor):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        code = sa.Column(sa.Integer, primary_key=True)

        def __init__(self):
            incrementor.value += 1
            self.id = incrementor.value
            self.code = incrementor.value
    return User


@pytest.fixture
def Event(Base):
    class Event(Base):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)

        object_type = sa.Column(sa.Unicode(255))
        object_id = sa.Column(sa.Integer, nullable=False)
        object_code = sa.Column(sa.Integer, nullable=False)

        object = generic_relationship(
            object_type, (object_id, object_code)
        )
    return Event


@pytest.fixture
def init_models(Building, User, Event):
    pass


class TestGenericRelationship(GenericRelationshipTestCase):

    def test_set_manual_and_get(self, session, Event, User):
        user = User()

        session.add(user)
        session.commit()

        event = Event()
        event.object_id = user.id
        event.object_type = type(user).__name__
        event.object_code = user.code

        assert event.object is None

        session.add(event)
        session.commit()

        assert event.object == user
