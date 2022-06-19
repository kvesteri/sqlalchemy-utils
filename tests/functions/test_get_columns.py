import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_columns


@pytest.fixture
def Building(Base):
    class Building(Base):
        __tablename__ = 'building'
        id = sa.Column('_id', sa.Integer, primary_key=True)
        name = sa.Column('_name', sa.Unicode(255))
    return Building


@pytest.fixture
def columns():
    return ['_id', '_name']


class TestGetColumns:
    def test_table(self, Building):
        assert isinstance(
            get_columns(Building.__table__),
            sa.sql.base.ImmutableColumnCollection
        )

    def test_instrumented_attribute(self, Building):
        assert get_columns(Building.id) == [Building.__table__.c._id]

    def test_column_property(self, Building):
        assert get_columns(Building.id.property) == [
            Building.__table__.c._id
        ]

    def test_column(self, Building):
        assert get_columns(Building.__table__.c._id) == [
            Building.__table__.c._id
        ]

    def test_declarative_class(self, Building, columns):
        assert [c.name for c in get_columns(Building).values()] == columns

    def test_declarative_object(self, Building, columns):
        assert [c.name for c in get_columns(Building()).values()] == columns

    def test_mapper(self, Building, columns):
        assert [
            c.name for c in get_columns(Building.__mapper__).values()
        ] == columns

    def test_class_alias(self, Building, columns):
        assert [
            c.name for c in get_columns(sa.orm.aliased(Building)).values()
        ] == columns

    def test_table_alias(self, Building, columns):
        alias = sa.orm.aliased(Building.__table__)
        assert [c.name for c in get_columns(alias).values()] == columns
