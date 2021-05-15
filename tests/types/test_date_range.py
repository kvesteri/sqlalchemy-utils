from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import DateRangeType

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
        during = sa.Column(DateRangeType)

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
class DateRangeTestCase:
    def test_nullify_range(self, create_booking):
        booking = create_booking(None)
        assert booking.during is None

    @pytest.mark.parametrize(
        ('date_range'),
        (
            [datetime(2015, 1, 1).date(), datetime(2015, 1, 3).date()],
            [datetime(2015, 1, 1).date(), inf],
            [-inf, datetime(2015, 1, 1).date()]
        )
    )
    def test_save_date_range(self, create_booking, date_range):
        booking = create_booking(date_range)
        assert booking.during.lower == date_range[0]
        assert booking.during.upper == date_range[1]

    def test_nullify_date_range(self, session, Booking):
        booking = Booking(
            during=intervals.DateInterval(
                [datetime(2015, 1, 1).date(), datetime(2015, 1, 3).date()]
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
        booking = Booking(during=datetime(2015, 1, 1).date())
        assert booking.during.lower == datetime(2015, 1, 1).date()
        assert booking.during.upper == datetime(2015, 1, 1).date()


@pytest.mark.usefixtures('postgresql_dsn')
class TestDateRangeOnPostgres(DateRangeTestCase):
    @pytest.mark.parametrize(
        ('date_range', 'length'),
        (
            (
                [datetime(2015, 1, 1).date(), datetime(2015, 1, 3).date()],
                timedelta(days=2)
            ),
            (
                [datetime(2015, 1, 1).date(), datetime(2015, 1, 1).date()],
                timedelta(days=0)
            ),
            ([-inf, datetime(2015, 1, 1).date()], None),
            ([datetime(2015, 1, 1).date(), inf], None),
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

    def test_literal_param(self, session, Booking):
        clause = Booking.during == [
            datetime(2015, 1, 1).date(),
            datetime(2015, 1, 3).date()
        ]
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == "booking.during = '[2015-01-01, 2015-01-03]'"
