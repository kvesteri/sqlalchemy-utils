from __future__ import unicode_literals
import six
from tests import TestCase


class GenericRelationshipTestCase(TestCase):
    def test_set_as_none(self):
        event = self.Event()
        event.object = None
        assert event.object is None

    def test_set_manual_and_get(self):
        user = self.User()

        self.session.add(user)
        self.session.commit()

        event = self.Event()
        event.object_id = user.id
        event.object_type = six.text_type(type(user).__name__)

        assert event.object is None

        self.session.add(event)
        self.session.commit()

        assert event.object == user

    def test_set_and_get(self):
        user = self.User()

        self.session.add(user)
        self.session.commit()

        event = self.Event(object=user)

        assert event.object_id == user.id
        assert event.object_type == type(user).__name__

        self.session.add(event)
        self.session.commit()

        assert event.object == user

    def test_compare_instance(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event = self.Event(object=user1)

        self.session.add(event)
        self.session.commit()

        assert event.object == user1
        assert event.object != user2

    def test_compare_query(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event = self.Event(object=user1)

        self.session.add(event)
        self.session.commit()

        q = self.session.query(self.Event)
        assert q.filter_by(object=user1).first() is not None
        assert q.filter_by(object=user2).first() is None
        assert q.filter(self.Event.object == user2).first() is None

    def test_compare_not_query(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event = self.Event(object=user1)

        self.session.add(event)
        self.session.commit()

        q = self.session.query(self.Event)
        assert q.filter(self.Event.object != user2).first() is not None

    def test_compare_type(self):
        user1 = self.User()
        user2 = self.User()

        self.session.add_all([user1, user2])
        self.session.commit()

        event1 = self.Event(object=user1)
        event2 = self.Event(object=user2)

        self.session.add_all([event1, event2])
        self.session.commit()

        statement = self.Event.object.is_type(self.User)
        q = self.session.query(self.Event).filter(statement)
        assert q.first() is not None
