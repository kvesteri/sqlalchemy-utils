try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import get_primary_keys


class TestGetPrimaryKeys(object):
    def setup_method(self, method):
        Base = declarative_base()

        class Building(Base):
            __tablename__ = 'building'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            name = sa.Column('_name', sa.Unicode(255))

        self.Building = Building

    def test_table(self):
        assert get_primary_keys(self.Building.__table__) == OrderedDict({
            '_id': self.Building.__table__.c._id
        })

    def test_declarative_class(self):
        assert get_primary_keys(self.Building) == OrderedDict({
            'id': self.Building.__table__.c._id
        })

    def test_declarative_object(self):
        assert get_primary_keys(self.Building()) == OrderedDict({
            'id': self.Building.__table__.c._id
        })

    def test_class_alias(self):
        alias = sa.orm.aliased(self.Building)
        assert get_primary_keys(alias) == OrderedDict({
            'id': self.Building.__table__.c._id
        })

    def test_table_alias(self):
        alias = sa.orm.aliased(self.Building.__table__)
        assert get_primary_keys(alias) == OrderedDict({
            '_id': alias.c._id
        })
