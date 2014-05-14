from pytest import raises
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import get_mapper


class TestGetMapper(object):
    def setup_method(self, method):
        self.Base = declarative_base()

        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)

        self.Building = Building

    def test_table(self):
        assert get_mapper(self.Building.__table__) == sa.inspect(self.Building)

    def test_declarative_class(self):
        assert (
            get_mapper(self.Building) ==
            sa.inspect(self.Building)
        )

    def test_declarative_object(self):
        assert (
            get_mapper(self.Building()) ==
            sa.inspect(self.Building)
        )

    def test_mapper(self):
        assert (
            get_mapper(self.Building.__mapper__) ==
            sa.inspect(self.Building)
        )

    def test_class_alias(self):
        assert (
            get_mapper(sa.orm.aliased(self.Building)) ==
            sa.inspect(self.Building)
        )

    def test_table_alias(self):
        alias = sa.orm.aliased(self.Building.__table__)
        assert (
            get_mapper(alias) ==
            sa.inspect(self.Building)
        )


class TestGetMapperWithMultipleMappersFound(object):
    def setup_method(self, method):
        Base = declarative_base()

        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)

        class BigBuilding(Building):
            pass

        self.Building = Building

    def test_table(self):
        with raises(ValueError):
            get_mapper(self.Building.__table__)

    def test_table_alias(self):
        alias = sa.orm.aliased(self.Building.__table__)
        with raises(ValueError):
            get_mapper(alias)


class TestGetMapperForTableWithoutMapper(object):
    def setup_method(self, method):
        metadata = sa.MetaData()
        self.building = sa.Table('building', metadata)

    def test_table(self):
        with raises(ValueError):
            get_mapper(self.building)

    def test_table_alias(self):
        alias = sa.orm.aliased(self.building)
        with raises(ValueError):
            get_mapper(alias)
