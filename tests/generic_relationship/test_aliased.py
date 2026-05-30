import pytest
import sqlalchemy as sa

from sqlalchemy_utils import generic_relationship


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
def init_models(User, Event):
    pass


class TestGenericRelationship(object):

    def test_compare_statement(self, session, User, Event):
        event_alias = sa.orm.aliased(Event)

        statemement_alias = event_alias.object.is_type(User)
        statemement = Event.object.is_type(User)

        assert (
            statemement_alias.compile().string !=
            statemement.compile().string
        )
