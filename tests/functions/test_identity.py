import sqlalchemy as sa
from sqlalchemy_utils.functions import identity
from tests import TestCase


class IdentityTestCase(TestCase):
    def test_for_transient_class_without_id(self):
        assert identity(self.Building()) == (None, )

    def test_for_transient_class_with_id(self):
        building = self.Building(name=u'Some building')
        self.session.add(building)
        self.session.flush()

        assert identity(building) == (building.id, )

    def test_identity_for_class(self):
        assert identity(self.Building) == (self.Building.id, )


class TestIdentity(IdentityTestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        self.Building = Building


class TestIdentityWithColumnAlias(IdentityTestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        self.Building = Building
