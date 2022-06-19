from copy import copy

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_column_key


@pytest.fixture
def Building(Base):
    class Building(Base):
        __tablename__ = 'building'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column('_name', sa.Unicode(255))
    return Building


@pytest.fixture
def Movie(Base):
    class Movie(Base):
        __tablename__ = 'movie'
        id = sa.Column(sa.Integer, primary_key=True)
    return Movie


class TestGetColumnKey:

    def test_supports_aliases(self, Building):
        assert (
            get_column_key(Building, Building.__table__.c.id) ==
            'id'
        )
        assert (
            get_column_key(Building, Building.__table__.c._name) ==
            'name'
        )

    def test_supports_vague_matching_of_column_objects(self, Building):
        column = copy(Building.__table__.c._name)
        assert get_column_key(Building, column) == 'name'

    def test_throws_value_error_for_unknown_column(self, Building, Movie):
        with pytest.raises(sa.orm.exc.UnmappedColumnError):
            get_column_key(Building, Movie.__table__.c.id)
