from __future__ import unicode_literals
import six
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import generic_relationship
from tests import TestCase


class TestGenericRelationship(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

        class UserHistory(self.Base):
            __tablename__ = 'user_history'
            id = sa.Column(sa.Integer, primary_key=True)

            transaction_id = sa.Column(sa.Integer, primary_key=True)

        class Event(self.Base):
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

        self.User = User
        self.UserHistory = UserHistory
        self.Event = Event

    def test_set_manual_and_get(self):
        user = self.User(id=1)
        history = self.UserHistory(id=1, transaction_id=1)
        self.session.add(user)
        self.session.add(history)
        self.session.commit()

        event = self.Event(transaction_id=1)
        event.object_id = user.id
        event.object_type = six.text_type(type(user).__name__)
        assert event.object is None

        self.session.add(event)
        self.session.commit()

        assert event.object == user
        assert event.object_version == history
