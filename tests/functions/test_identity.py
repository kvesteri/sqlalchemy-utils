import sqlalchemy as sa
from sqlalchemy_utils.functions import identity
from tests import TestCase


class TestIdentity(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        self.Building = Building

    def test_for_transient_class_without_id(self):
        assert identity(self.Building()) == (None,)
