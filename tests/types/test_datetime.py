import datetime
import sqlalchemy as sa
from sqlalchemy_utils.types import datetime as dt
from tests import TestCase


class TestDateTypeType(TestCase):
    def create_models(self):
        class Visitor(self.Base):
            __tablename__ = 'visitor'
            id = sa.Column(sa.Integer, primary_key=True)
            timestamp = sa.Column(
                dt.DateTimeType()
            )

        self.Visitor = Visitor

    def test_parameter_processing(self):
        now = datetime.datetime.utcnow()
        visitor = self.Visitor(
            timestamp=now,
        )

        self.session.add(visitor)
        self.session.commit()

        fetched_visitor = self.session.query(self.Visitor).filter_by(
            timestamp=now,
        ).first()
        assert visitor == fetched_visitor
        assert fetched_visitor.timestamp == now
