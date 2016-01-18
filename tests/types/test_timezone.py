import pytest
import sqlalchemy as sa

from sqlalchemy_utils.types import timezone


@pytest.fixture
def Visitor(Base):
    class Visitor(Base):
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
    return Visitor


@pytest.fixture
def init_models(Visitor):
    pass


class TestTimezoneType(object):

    def test_parameter_processing(self, session, Visitor):
        visitor = Visitor(
            timezone_dateutil=u'America/Los_Angeles',
            timezone_pytz=u'America/Los_Angeles'
        )

        session.add(visitor)
        session.commit()

        visitor_dateutil = session.query(Visitor).filter_by(
            timezone_dateutil=u'America/Los_Angeles'
        ).first()
        visitor_pytz = session.query(Visitor).filter_by(
            timezone_pytz=u'America/Los_Angeles'
        ).first()

        assert visitor_dateutil is not None
        assert visitor_pytz is not None
