import sqlalchemy as sa
from sqlalchemy_utils import get_columns
from tests import TestCase


class TestGetColumns(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            name = sa.Column('_name', sa.Unicode(255))

        self.Building = Building

    def test_table(self):
        assert isinstance(
            get_columns(self.Building.__table__),
            sa.sql.base.ImmutableColumnCollection
        )

    def test_declarative_class(self):
        assert isinstance(
            get_columns(self.Building),
            sa.util._collections.OrderedProperties
        )

    def test_declarative_object(self):
        assert isinstance(
            get_columns(self.Building()),
            sa.util._collections.OrderedProperties
        )

    def test_mapper(self):
        assert isinstance(
            get_columns(self.Building.__mapper__),
            sa.util._collections.OrderedProperties
        )

    def test_class_alias(self):
        assert isinstance(
            get_columns(sa.orm.aliased(self.Building)),
            sa.util._collections.OrderedProperties
        )

    def test_table_alias(self):
        alias = sa.orm.aliased(self.Building.__table__)
        assert isinstance(
            get_columns(alias),
            sa.sql.base.ImmutableColumnCollection
        )
