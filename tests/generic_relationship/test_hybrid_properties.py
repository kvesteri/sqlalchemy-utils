import pytest
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy_utils import generic_relationship


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
    return User


@pytest.fixture
def UserHistory(Base):
    class UserHistory(Base):
        __tablename__ = 'user_history'
        id = sa.Column(sa.Integer, primary_key=True)

        transaction_id = sa.Column(sa.Integer, primary_key=True)
    return UserHistory


@pytest.fixture
def Event(Base):
    class Event(Base):
        __tablename__ = 'event'
        id = sa.Column(sa.Integer, primary_key=True)

        transaction_id = sa.Column(sa.Integer)

        object_type = sa.Column(sa.Unicode(255))
        object_id = sa.Column(sa.Integer, nullable=False)

        object = generic_relationship(
            object_type, object_id
        )

        @hybrid_property
        def object_version_type(self):
            return self.object_type + 'History'

        @object_version_type.expression
        def object_version_type(cls):
            return sa.func.concat(cls.object_type, 'History')

        object_version = generic_relationship(
            object_version_type, (object_id, transaction_id)
        )
    return Event


@pytest.fixture
def init_models(User, UserHistory, Event):
    pass


class TestGenericRelationship:

    def test_set_manual_and_get(self, session, User, UserHistory, Event):
        user = User(id=1)
        history = UserHistory(id=1, transaction_id=1)
        session.add(user)
        session.add(history)
        session.commit()

        event = Event(transaction_id=1)
        event.object_id = user.id
        event.object_type = type(user).__name__
        assert event.object is None

        session.add(event)
        session.commit()

        assert event.object == user
        assert event.object_version == history
