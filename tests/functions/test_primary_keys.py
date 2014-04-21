try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import sqlalchemy as sa
from sqlalchemy_utils import primary_keys
from tests import TestCase


class TestPrimaryKeys(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            name = sa.Column('_name', sa.Unicode(255))

        self.Building = Building

    def test_table(self):
        assert primary_keys(self.Building.__table__) == OrderedDict({
            '_id': self.Building.__table__.c._id
        })

    def test_declarative_class(self):
        assert primary_keys(self.Building) == OrderedDict({
            'id': self.Building.__table__.c._id
        })

    def test_declarative_object(self):
        assert primary_keys(self.Building()) == OrderedDict({
            'id': self.Building.__table__.c._id
        })
