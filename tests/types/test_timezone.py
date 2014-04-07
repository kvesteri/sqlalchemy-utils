from pytest import mark
import six
import sqlalchemy as sa
from sqlalchemy_utils.types import timezone
from tests import TestCase

import dateutil
import pytz


class TestTimezoneType(TestCase):
    def create_models(self):
        class Visitor(self.Base):
            __tablename__ = 'visitor'
            id = sa.Column(sa.Integer, primary_key=True)
            timezone_dateutil = sa.Column(
                timezone.TimezoneType(backend='dateutil')
            )
            timezone_pytz = sa.Column(
                timezone.TimezoneType(backend='pytz')
            )

            def __repr__(self):
                return 'Visitor(%r)' % self.id

        self.Visitor = Visitor

    def test_parameter_processing(self):
        visitor = self.Visitor(
            timezone_dateutil=u'America/Los_Angeles',
            timezone_pytz=u'America/Los_Angeles'
        )

        self.session.add(visitor)
        self.session.commit()

        visitor_dateutil = self.session.query(self.Visitor).filter_by(
            timezone_dateutil=u'America/Los_Angeles'
        ).first()
        visitor_pytz = self.session.query(self.Visitor).filter_by(
            timezone_pytz=u'America/Los_Angeles'
        ).first()

        assert visitor_dateutil is not None
        assert visitor_pytz is not None
