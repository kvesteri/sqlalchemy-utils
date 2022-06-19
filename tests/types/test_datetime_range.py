from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import DateTimeRangeType
from sqlalchemy_utils.compat import _select_args

intervals = None
inf = 0
try:
    import intervals
    from infinity import inf
except ImportError:
    pass


@pytest.fixture
def Booking(Base):
    class Booking(Base):
        __tablename__ = 'booking'
        id = sa.Column(sa.Integer, primary_key=True)
        during = sa.Column(DateTimeRangeType)

    return Booking


@pytest.fixture
def create_booking(session, Booking):
    def create_booking(date_range):
        booking = Booking(
            during=date_range
        )
        session.add(booking)
        session.commit()
        return session.query(Booking).first()
    return create_booking


@pytest.fixture
def init_models(Booking):
    pass


@pytest.mark.skipif('intervals is None')
class DateTimeRangeTestCase:
    def test_nullify_range(self, create_booking):
        booking = create_booking(None)
        assert booking.during is None

    @pytest.mark.parametrize(
        ('date_range'),
        (
            [datetime(2015, 1, 1), datetime(2015, 1, 3)],
            [datetime(2015, 1, 1), inf],
            [-inf, datetime(2015, 1, 1)]
        )
    )
    def test_save_date_range(self, create_booking, date_range):
        booking = create_booking(date_range)
        assert booking.during.lower == date_range[0]
        assert booking.during.upper == date_range[1]

    def test_nullify_date_range(self, session, Booking):
        booking = Booking(
            during=intervals.DateInterval(
                [datetime(2015, 1, 1), datetime(2015, 1, 3)]
            )
        )

        session.add(booking)
        session.commit()

        booking = session.query(Booking).first()
        booking.during = None
        session.commit()

        booking = session.query(Booking).first()
        assert booking.during is None

    def test_integer_coercion(self, Booking):
        booking = Booking(during=datetime(2015, 1, 1))
        assert booking.during.lower == datetime(2015, 1, 1)
        assert booking.during.upper == datetime(2015, 1, 1)

    def test_compilation(self, session, Booking):
        query = sa.select(*_select_args(Booking.during))

        # the type should be cacheable and not throw exception
        session.execute(query)


@pytest.mark.usefixtures('postgresql_dsn')
class TestDateTimeRangeOnPostgres(DateTimeRangeTestCase):
    @pytest.mark.parametrize(
        ('date_range', 'length'),
        (
            (
                [datetime(2015, 1, 1), datetime(2015, 1, 3)],
                timedelta(days=2)
            ),
            (
                [datetime(2015, 1, 1), datetime(2015, 1, 1)],
                timedelta(days=0)
            ),
            ([-inf, datetime(2015, 1, 1)], None),
            ([datetime(2015, 1, 1), inf], None),
        )
    )
    def test_length(
        self,
        session,
        Booking,
        create_booking,
        date_range,
        length
    ):
        create_booking(date_range)
        query = (
            session.query(Booking.during.length)
        )
        assert query.scalar() == length
