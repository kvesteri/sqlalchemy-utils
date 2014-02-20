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

    def create_building(self, number_range):
        building = self.Building(
            persons_at_night=number_range
        )

        self.session.add(building)
        self.session.commit()
        return self.session.query(self.Building).first()

    def test_nullify_range(self):
        building = self.create_building(None)
        assert building.persons_at_night == None

    def test_update_with_none(self):
        interval = intervals.IntInterval('(,)')
        building = self.create_building(interval)
        building.persons_at_night = None
        assert building.persons_at_night is None
        self.session.commit()
        assert building.persons_at_night is None

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
        )
    )
    def test_save_number_range(self, number_range):
        building = self.create_building(number_range)
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper == 3

    def test_infinite_upper_bound(self):
        building = self.create_building([1, inf])
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper == inf

    def test_infinite_lower_bound(self):
        building = self.create_building([-inf, 1])
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


class TestIntRangeTypeOnPostgres(NumberRangeTestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
            (0, 4)
        )
    )
    def test_eq_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night == number_range)
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [[1, 3]],
            ['1 - 3'],
            [(0, 4)],
        )
    )
    def test_in_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night.in_(number_range))
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
            (0, 4),
        )
    )
    def test_rshift_operator(self, number_range):
        self.create_building([5, 6])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night >> number_range)
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
            (0, 4),
        )
    )
    def test_lshift_operator(self, number_range):
        self.create_building([-1, 0])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night << number_range)
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
            (1, 3),
            2
        )
    )
    def test_contains_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night.contains(number_range))
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
            (0, 8),
            (-inf, inf)
        )
    )
    def test_contained_by_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night.contained_by(number_range))
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [2, 5],
            '0 - 2',
            0
        )
    )
    def test_not_in_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(~ self.Building.persons_at_night.in_([number_range]))
        )
        assert query.count()

    def test_eq_with_query_arg(self):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(
                self.Building.persons_at_night ==
                self.session.query(
                    self.Building.persons_at_night)
                ).order_by(self.Building.persons_at_night).limit(1)
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [1, 2],
            '1 - 3',
            (0, 4),
            [0, 3],
            0,
            1,
        )
    )
    def test_ge_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night >= number_range)
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [0, 2],
            0,
            [-inf, 2]
        )
    )
    def test_gt_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night > number_range)
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [1, 4],
            4,
            [2, inf]
        )
    )
    def test_le_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night <= number_range)
        )
        assert query.count()

    @mark.parametrize(
        'number_range',
        (
            [2, 4],
            4,
            [1, inf]
        )
    )
    def test_lt_operator(self, number_range):
        self.create_building([1, 3])
        query = (
            self.session.query(self.Building)
            .filter(self.Building.persons_at_night < number_range)
        )
        assert query.count()


class TestNumberRangeTypeOnSqlite(NumberRangeTestCase):
    pass
