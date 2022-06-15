import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_primary_keys

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


@pytest.fixture
def Building(Base):
    class Building(Base):
        __tablename__ = 'building'
        id = sa.Column('_id', sa.Integer, primary_key=True)
        name = sa.Column('_name', sa.Unicode(255))
    return Building


class TestGetPrimaryKeys:

    def test_table(self, Building):
        assert get_primary_keys(Building.__table__) == OrderedDict({
            '_id': Building.__table__.c._id
        })

    def test_declarative_class(self, Building):
        assert get_primary_keys(Building) == OrderedDict({
            'id': Building.__table__.c._id
        })

    def test_declarative_object(self, Building):
        assert get_primary_keys(Building()) == OrderedDict({
            'id': Building.__table__.c._id
        })

    def test_class_alias(self, Building):
        alias = sa.orm.aliased(Building)
        assert get_primary_keys(alias) == OrderedDict({
            'id': Building.__table__.c._id
        })

    def test_table_alias(self, Building):
        alias = sa.orm.aliased(Building.__table__)
        assert get_primary_keys(alias) == OrderedDict({
            '_id': alias.c._id
        })
