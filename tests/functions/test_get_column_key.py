from pytest import raises

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import get_column_key


class TestGetColumnKey(object):
    def setup_method(self, method):
        Base = declarative_base()

        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column('_name', sa.Unicode(255))

        self.Building = Building

    def test_supports_aliases(self):
        assert (
            get_column_key(self.Building, self.Building.__table__.c.id)
            ==
            'id'
        )
        assert (
            get_column_key(self.Building, self.Building.__table__.c._name)
            ==
            'name'
        )

    def test_throws_value_error_for_unknown_column(self):
        with raises(ValueError):
            get_column_key(self.Building, 'unknown')
