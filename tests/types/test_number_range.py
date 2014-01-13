from pytest import mark
import sqlalchemy as sa
intervals = None
try:
    import intervals
except ImportError:
    pass
from tests import TestCase
from infinity import inf
from sqlalchemy_utils import IntRangeType


@mark.skipif('intervals is None')
class NumberRangeTestCase(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            persons_at_night = sa.Column(IntRangeType)

            def __repr__(self):
                return 'Building(%r)' % self.id

        self.Building = Building

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
        )
    )
    def test_save_number_range(self, number_range):
        building = self.Building(
            persons_at_night=number_range
        )

        self.session.add(building)
        self.session.commit()
        self.session.expire(building)
        building = self.session.query(self.Building).first()
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper == 3

    def test_infinite_upper_bound(self):
        building = self.Building(
            persons_at_night=intervals.IntInterval([1, inf])
        )
        self.session.add(building)
        self.session.commit()

        building = self.session.query(self.Building).first()
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper == inf

    def test_infinite_lower_bound(self):
        building = self.Building(
            persons_at_night=intervals.IntInterval([-inf, 1])
        )
        self.session.add(building)
        self.session.commit()
        building = self.session.query(self.Building).first()
        assert building.persons_at_night.lower == -inf
        assert building.persons_at_night.upper == 1

    def test_nullify_number_range(self):
        building = self.Building(
            persons_at_night=intervals.IntInterval([1, 3])
        )

        self.session.add(building)
        self.session.commit()

        building = self.session.query(self.Building).first()
        building.persons_at_night = None
        self.session.commit()

        building = self.session.query(self.Building).first()
        assert building.persons_at_night is None

    def test_string_coercion(self):
        building = self.Building(persons_at_night='[12, 18]')

        assert isinstance(building.persons_at_night, intervals.IntInterval)

    def test_integer_coercion(self):
        building = self.Building(persons_at_night=15)
        assert building.persons_at_night.lower == 15
        assert building.persons_at_night.upper == 15



class TestNumberRangeTypeOnPostgres(NumberRangeTestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'


class TestNumberRangeTypeOnSqlite(NumberRangeTestCase):
    pass
