import pytest
import sqlalchemy as sa

from sqlalchemy_utils import table_name


@pytest.fixture
def Building(Base):
    class Building(Base):
        __tablename__ = 'building'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
    return Building


@pytest.fixture
def init_models(Base):
    pass


class TestTableName:

    def test_class(self, Building):
        assert table_name(Building) == 'building'
        del Building.__tablename__
        assert table_name(Building) == 'building'

    def test_attribute(self, Building):
        assert table_name(Building.id) == 'building'
        assert table_name(Building.name) == 'building'

    def test_target(self, Building):
        assert table_name(Building()) == 'building'
