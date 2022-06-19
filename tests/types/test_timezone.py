import pytest
import pytz
import sqlalchemy as sa
from dateutil.zoneinfo import get_zonefile_instance, tzfile

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from sqlalchemy_utils.compat import _select_args
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
        timezone_zoneinfo = sa.Column(
            timezone.TimezoneType(backend='zoneinfo')
        )

        def __repr__(self):
            return 'Visitor(%r)' % self.id
    return Visitor


@pytest.fixture
def init_models(Visitor):
    pass


class TestTimezoneType:
    def test_parameter_processing(self, session, Visitor):
        visitor = Visitor(
            timezone_dateutil='America/Los_Angeles',
            timezone_pytz='America/Los_Angeles',
            timezone_zoneinfo='America/Los_Angeles'
        )

        session.add(visitor)
        session.commit()

        visitor_dateutil = session.query(Visitor).filter_by(
            timezone_dateutil='America/Los_Angeles'
        ).first()
        visitor_pytz = session.query(Visitor).filter_by(
            timezone_pytz='America/Los_Angeles'
        ).first()
        visitor_zoneinfo = session.query(Visitor).filter_by(
            timezone_zoneinfo='America/Los_Angeles'
        ).first()

        assert visitor_dateutil is not None
        assert visitor_pytz is not None
        assert visitor_zoneinfo is not None

    def test_compilation(self, Visitor, session):
        query = sa.select(*_select_args(Visitor.timezone_pytz))
        # the type should be cacheable and not throw exception
        session.execute(query)


TIMEZONE_BACKENDS = ['dateutil', 'pytz', 'zoneinfo']


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


@pytest.mark.parametrize('zone', get_zonefile_instance().zones.keys())
def test_can_coerce_string_for_dateutil_zone(zone):
    tzcol = TimezoneType(backend='dateutil')
    assert isinstance(tzcol._coerce(zone), tzfile)


@pytest.mark.parametrize('zone', zoneinfo.available_timezones())
def test_can_coerce_string_for_zoneinfo_zone(zone):
    tzcol = TimezoneType(backend='zoneinfo')
    assert str(tzcol._coerce(zone)) == zone


@pytest.mark.parametrize('backend', TIMEZONE_BACKENDS)
def test_can_coerce_and_raise_UnknownTimeZoneError_or_ValueError(backend):
    tzcol = TimezoneType(backend=backend)
    exceptions = (
        ValueError,
        pytz.exceptions.UnknownTimeZoneError,
        zoneinfo.ZoneInfoNotFoundError
    )
    with pytest.raises(exceptions):
        tzcol._coerce('SolarSystem/Mars')
    with pytest.raises(exceptions):
        tzcol._coerce('')


@pytest.mark.parametrize('backend', TIMEZONE_BACKENDS)
def test_can_coerce_None(backend):
    tzcol = TimezoneType(backend=backend)
    assert tzcol._coerce(None) is None
