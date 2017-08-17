import pytest
import pytz
import sqlalchemy as sa
from dateutil.zoneinfo import getzoneinfofile_stream, tzfile, ZoneInfoFile

from sqlalchemy_utils.types import timezone, TimezoneType


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


TIMEZONE_BACKENDS = ['dateutil', 'pytz']


def test_can_coerce_pytz_DstTzInfo():
    tzcol = TimezoneType(backend='pytz')
    tz = pytz.timezone('America/New_York')
    assert isinstance(tz, pytz.tzfile.DstTzInfo)
    assert tzcol._coerce(tz) is tz


def test_can_coerce_pytz_StaticTzInfo():
    tzcol = TimezoneType(backend='pytz')
    tz = pytz.timezone('Pacific/Truk')
    assert tzcol._coerce(tz) is tz


@pytest.mark.parametrize('zone', pytz.all_timezones)
def test_can_coerce_string_for_pytz_zone(zone):
    tzcol = TimezoneType(backend='pytz')
    assert tzcol._coerce(zone).zone == zone


@pytest.mark.parametrize(
    'zone', ZoneInfoFile(getzoneinfofile_stream()).zones.keys())
def test_can_coerce_string_for_dateutil_zone(zone):
    tzcol = TimezoneType(backend='dateutil')
    assert isinstance(tzcol._coerce(zone), tzfile)


@pytest.mark.parametrize('backend', TIMEZONE_BACKENDS)
def test_can_coerce_and_raise_UnknownTimeZoneError_or_ValueError(backend):
    tzcol = TimezoneType(backend=backend)
    with pytest.raises((ValueError, pytz.exceptions.UnknownTimeZoneError)):
        tzcol._coerce('SolarSystem/Mars')
    with pytest.raises((ValueError, pytz.exceptions.UnknownTimeZoneError)):
        tzcol._coerce('')


@pytest.mark.parametrize('backend', TIMEZONE_BACKENDS)
def test_can_coerce_None(backend):
    tzcol = TimezoneType(backend=backend)
    assert tzcol._coerce(None) is None
