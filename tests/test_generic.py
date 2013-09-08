import sqlalchemy as sa
from sqlalchemy import orm
from tests import TestCase
from sqlalchemy_utils import generic_relationship


class TestGenericForiegnKey(TestCase):

    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)

        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

            building_id = sa.Column(sa.Integer, sa.ForeignKey(Building.id), name='buildingID')

            building = orm.relationship(Building)

        class Event(self.Base):
            __tablename__ = 'event'
            id = sa.Column(sa.Integer, primary_key=True)

            object_type = sa.Column(sa.Unicode(255), name="objectType")
            object_id = sa.Column(sa.Integer, nullable=False)

            object = generic_relationship(object_type, object_id)

        self.Building = Building
        self.User = User
        self.Event = Event

    def test_set_manual_and_get(self):
        user = self.User()

        self.session.add(user)
        self.session.commit()

        event = self.Event()
        event.object_id = user.id
        event.object_type = type(user).__tablename__

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
        assert event.object_type == type(user).__tablename__

        self.session.add(event)
        self.session.commit()

        assert event.object == user
