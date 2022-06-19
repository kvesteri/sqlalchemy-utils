import pytest
import sqlalchemy as sa

from sqlalchemy_utils.functions import identity


class IdentityTestCase:

    @pytest.fixture
    def init_models(self, Building):
        pass

    def test_for_transient_class_without_id(self, Building):
        assert identity(Building()) == (None, )

    def test_for_transient_class_with_id(self, session, Building):
        building = Building(name='Some building')
        session.add(building)
        session.flush()

        assert identity(building) == (building.id, )

    def test_identity_for_class(self, Building):
        assert identity(Building) == (Building.id, )


class TestIdentity(IdentityTestCase):

    @pytest.fixture
    def Building(self, Base):
        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return Building


class TestIdentityWithColumnAlias(IdentityTestCase):

    @pytest.fixture
    def Building(self, Base):
        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return Building
