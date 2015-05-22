from datetime import datetime, timedelta

import sqlalchemy as sa
from pytest import mark

from sqlalchemy_utils import DateTimeRangeType
from tests import TestCase

intervals = None
inf = 0
try:
    import intervals
    from infinity import inf
except ImportError:
    pass


@mark.skipif('intervals is None')
class DateRangeTestCase(TestCase):
    def create_models(self):
        class Booking(self.Base):
            __tablename__ = 'booking'
            id = sa.Column(sa.Integer, primary_key=True)
            during = sa.Column(DateTimeRangeType)

        self.Booking = Booking

    def create_booking(self, date_range):
        booking = self.Booking(
            during=date_range
        )

        self.session.add(booking)
        self.session.commit()
        return self.session.query(self.Booking).first()

    def test_nullify_range(self):
        booking = self.create_booking(None)
        assert booking.during is None

    @mark.parametrize(
        ('date_range'),
        (
            [datetime(2015, 1, 1), datetime(2015, 1, 3)],
            [datetime(2015, 1, 1), inf],
            [-inf, datetime(2015, 1, 1)]
        )
    )
    def test_save_date_range(self, date_range):
        booking = self.create_booking(date_range)
        assert booking.during.lower == date_range[0]
        assert booking.during.upper == date_range[1]

    def test_nullify_date_range(self):
        booking = self.Booking(
            during=intervals.DateInterval(
                [datetime(2015, 1, 1), datetime(2015, 1, 3)]
            )
        )

        self.session.add(booking)
        self.session.commit()

        booking = self.session.query(self.Booking).first()
        booking.during = None
        self.session.commit()

        booking = self.session.query(self.Booking).first()
        assert booking.during is None

    def test_integer_coercion(self):
        booking = self.Booking(during=datetime(2015, 1, 1))
        assert booking.during.lower == datetime(2015, 1, 1)
        assert booking.during.upper == datetime(2015, 1, 1)


class TestDateRangeOnPostgres(DateRangeTestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    @mark.parametrize(
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
    def test_length(self, date_range, length):
        self.create_booking(date_range)
        query = (
            self.session.query(self.Booking.during.length)
        )
        assert query.scalar() == length
