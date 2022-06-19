import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_mapper
from sqlalchemy_utils.functions.orm import _get_query_compile_state


class TestGetMapper:

    @pytest.fixture
    def Building(self, Base):
        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
        return Building

    def test_table(self, Building):
        assert get_mapper(Building.__table__) == sa.inspect(Building)

    def test_declarative_class(self, Building):
        assert (
            get_mapper(Building) ==
            sa.inspect(Building)
        )

    def test_declarative_object(self, Building):
        assert (
            get_mapper(Building()) ==
            sa.inspect(Building)
        )

    def test_mapper(self, Building):
        assert (
            get_mapper(Building.__mapper__) ==
            sa.inspect(Building)
        )

    def test_class_alias(self, Building):
        assert (
            get_mapper(sa.orm.aliased(Building)) ==
            sa.inspect(Building)
        )

    def test_instrumented_attribute(self, Building):
        assert (
            get_mapper(Building.id) == sa.inspect(Building)
        )

    def test_table_alias(self, Building):
        alias = sa.orm.aliased(Building.__table__)
        assert (
            get_mapper(alias) ==
            sa.inspect(Building)
        )

    def test_column(self, Building):
        assert (
            get_mapper(Building.__table__.c.id) ==
            sa.inspect(Building)
        )

    def test_column_of_an_alias(self, Building):
        assert (
            get_mapper(sa.orm.aliased(Building.__table__).c.id) ==
            sa.inspect(Building)
        )


class TestGetMapperWithQueryEntities:

    @pytest.fixture
    def Building(self, Base):
        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
        return Building

    @pytest.fixture
    def init_models(self, Building):
        pass

    def test_mapper_entity_with_mapper(self, session, Building):
        query = session.query(Building.__mapper__)
        entity = _get_query_compile_state(query)._entities[0]
        assert get_mapper(entity) == sa.inspect(Building)

    def test_mapper_entity_with_class(self, session, Building):
        query = session.query(Building)
        entity = _get_query_compile_state(query)._entities[0]
        assert get_mapper(entity) == sa.inspect(Building)

    def test_column_entity(self, session, Building):
        query = session.query(Building.id)
        entity = _get_query_compile_state(query)._entities[0]
        assert get_mapper(entity) == sa.inspect(Building)


class TestGetMapperWithMultipleMappersFound:

    @pytest.fixture
    def Building(self, Base):
        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)

        class BigBuilding(Building):
            pass

        return Building

    def test_table(self, Building):
        with pytest.raises(ValueError):
            get_mapper(Building.__table__)

    def test_table_alias(self, Building):
        alias = sa.orm.aliased(Building.__table__)
        with pytest.raises(ValueError):
            get_mapper(alias)


class TestGetMapperForTableWithoutMapper:

    @pytest.fixture
    def building(self):
        metadata = sa.MetaData()
        return sa.Table('building', metadata)

    def test_table(self, building):
        with pytest.raises(ValueError):
            get_mapper(building)

    def test_table_alias(self, building):
        alias = sa.orm.aliased(building)
        with pytest.raises(ValueError):
            get_mapper(alias)
