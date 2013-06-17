import sqlalchemy as sa
from sqlalchemy_utils import table_name
from tests import TestCase


class TestTableName(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        self.Building = Building

    def test_table_name(self):
        assert table_name(self.Building) == 'building'
        del self.Building.__tablename__
        assert table_name(self.Building) == 'building'
