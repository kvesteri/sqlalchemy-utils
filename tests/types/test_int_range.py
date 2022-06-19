import pytest
import sqlalchemy as sa

from sqlalchemy_utils import IntRangeType
from sqlalchemy_utils.compat import _select_args, get_scalar_subquery

intervals = None
inf = -1
try:
    import intervals
    from infinity import inf
except ImportError:
    pass


@pytest.fixture
def Building(Base):
    class Building(Base):
        __tablename__ = 'building'
        id = sa.Column(sa.Integer, primary_key=True)
        persons_at_night = sa.Column(IntRangeType)

        def __repr__(self):
            return 'Building(%r)' % self.id
    return Building


@pytest.fixture
def init_models(Building):
    pass


@pytest.fixture
def create_building(session, Building):
    def create_building(number_range):
        building = Building(
            persons_at_night=number_range
        )

        session.add(building)
        session.commit()
        return session.query(Building).first()
    return create_building


@pytest.mark.skipif('intervals is None')
class NumberRangeTestCase:

    def test_nullify_range(self, create_building):
        building = create_building(None)
        assert building.persons_at_night is None

    def test_update_with_none(self, session, create_building):
        interval = intervals.IntInterval([None, None])
        building = create_building(interval)
        building.persons_at_night = None
        assert building.persons_at_night is None
        session.commit()
        assert building.persons_at_night is None

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 3],
            (0, 4),
        )
    )
    def test_save_number_range(self, create_building, number_range):
        building = create_building(number_range)
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper == 3

    def test_infinite_upper_bound(self, create_building):
        building = create_building([1, inf])
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper == inf

    def test_infinite_lower_bound(self, create_building):
        building = create_building([-inf, 1])
        assert building.persons_at_night.lower == -inf
        assert building.persons_at_night.upper == 1

    def test_nullify_number_range(self, session, Building):
        building = Building(
            persons_at_night=intervals.IntInterval([1, 3])
        )

        session.add(building)
        session.commit()

        building = session.query(Building).first()
        building.persons_at_night = None
        session.commit()

        building = session.query(Building).first()
        assert building.persons_at_night is None

    def test_integer_coercion(self, Building):
        building = Building(persons_at_night=15)
        assert building.persons_at_night.lower == 15
        assert building.persons_at_night.upper == 15

    def test_compilation(self, session, Building):
        query = sa.select(*_select_args(Building.persons_at_night))

        # the type should be cacheable and not throw exception
        session.execute(query)


@pytest.mark.usefixtures('postgresql_dsn')
class TestIntRangeTypeOnPostgres(NumberRangeTestCase):
    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 3],
            (0, 4)
        )
    )
    def test_eq_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night == number_range)
        )
        assert query.count()

    @pytest.mark.parametrize(
        ('number_range', 'length'),
        (
            ([1, 3], 2),
            ([1, 1], 0),
            ([-1, 1], 2),
            ([-inf, 1], None),
            ([0, inf], None),
            ([0, 0], 0),
            ([-3, -1], 2)
        )
    )
    def test_length(
        self,
        session,
        Building,
        create_building,
        number_range,
        length
    ):
        create_building(number_range)
        query = (
            session.query(Building.persons_at_night.length)
        )
        assert query.scalar() == length

    @pytest.mark.parametrize(
        'number_range',
        (
            [[1, 3]],
            [(0, 4)],
        )
    )
    def test_in_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night.in_(number_range))
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 3],
            (0, 4),
        )
    )
    def test_rshift_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([5, 6])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night >> number_range)
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 3],
            (0, 4),
        )
    )
    def test_lshift_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([-1, 0])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night << number_range)
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 3],
            (1, 3),
            2
        )
    )
    def test_contains_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night.contains(number_range))
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 3],
            (0, 8),
            (-inf, inf)
        )
    )
    def test_contained_by_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night.contained_by(number_range))
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [2, 5],
            0
        )
    )
    def test_not_in_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(~ Building.persons_at_night.in_([number_range]))
        )
        assert query.count()

    def test_eq_with_query_arg(self, session, Building, create_building):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(
                Building.persons_at_night ==
                get_scalar_subquery(session.query(Building.persons_at_night))
            ).order_by(Building.persons_at_night).limit(1)
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 2],
            (0, 4),
            [0, 3],
            0,
            1,
        )
    )
    def test_ge_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night >= number_range)
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [0, 2],
            0,
            [-inf, 2]
        )
    )
    def test_gt_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night > number_range)
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 4],
            4,
            [2, inf]
        )
    )
    def test_le_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night <= number_range)
        )
        assert query.count()

    @pytest.mark.parametrize(
        'number_range',
        (
            [2, 4],
            4,
            [1, inf]
        )
    )
    def test_lt_operator(
        self,
        session,
        Building,
        create_building,
        number_range
    ):
        create_building([1, 3])
        query = (
            session.query(Building)
            .filter(Building.persons_at_night < number_range)
        )
        assert query.count()

    def test_literal_param(self, session, Building):
        clause = Building.persons_at_night == [1, 3]
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == "building.persons_at_night = '[1, 3]'"


class TestNumberRangeTypeOnSqlite(NumberRangeTestCase):
    pass
