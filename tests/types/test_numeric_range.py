from decimal import Decimal

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import NumericRangeType
from sqlalchemy_utils.compat import _select_args

intervals = None
inf = 0
try:
    import intervals
    from infinity import inf
except ImportError:
    pass


@pytest.fixture
def create_car(session, Car):
    def create_car(number_range):
        car = Car(
            price_range=number_range
        )

        session.add(car)
        session.commit()
        return session.query(Car).first()
    return create_car


@pytest.mark.skipif('intervals is None')
class NumericRangeTestCase:

    @pytest.fixture
    def Car(self, Base):
        class Car(Base):
            __tablename__ = 'car'
            id = sa.Column(sa.Integer, primary_key=True)
            price_range = sa.Column(NumericRangeType)

        return Car

    @pytest.fixture
    def init_models(self, Car):
        pass

    def test_nullify_range(self, create_car):
        car = create_car(None)
        assert car.price_range is None

    @pytest.mark.parametrize(
        'number_range',
        (
            [1, 3],
            (1, 3)
        )
    )
    def test_save_number_range(self, create_car, number_range):
        car = create_car(number_range)
        assert car.price_range.lower == 1
        assert car.price_range.upper == 3

    def test_infinite_upper_bound(self, create_car):
        car = create_car([1, inf])
        assert car.price_range.lower == 1
        assert car.price_range.upper == inf

    def test_infinite_lower_bound(self, create_car):
        car = create_car([-inf, 1])
        assert car.price_range.lower == -inf
        assert car.price_range.upper == 1

    def test_nullify_number_range(self, session, Car):
        car = Car(
            price_range=intervals.DecimalInterval([1, 3])
        )

        session.add(car)
        session.commit()

        car = session.query(Car).first()
        car.price_range = None
        session.commit()

        car = session.query(Car).first()
        assert car.price_range is None

    def test_integer_coercion(self, Car):
        car = Car(price_range=15)
        assert car.price_range.lower == 15
        assert car.price_range.upper == 15

    def test_compilation(self, session, Car):
        query = sa.select(*_select_args(Car.price_range))

        # the type should be cacheable and not throw exception
        session.execute(query)


@pytest.mark.usefixtures('postgresql_dsn')
class TestNumericRangeOnPostgres(NumericRangeTestCase):

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
    def test_length(self, session, Car, create_car, number_range, length):
        create_car(number_range)
        query = (
            session.query(Car.price_range.length)
        )
        assert query.scalar() == length

    def test_literal_param(self, session, Car):
        clause = Car.price_range == [1, 3]
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == "car.price_range = '[1, 3]'"


@pytest.mark.skipif('intervals is None')
class TestNumericRangeWithStep:
    @pytest.fixture
    def Car(self, Base):
        class Car(Base):
            __tablename__ = 'car'
            id = sa.Column(sa.Integer, primary_key=True)
            price_range = sa.Column(NumericRangeType(step=Decimal('0.5')))
        return Car

    @pytest.fixture
    def init_models(self, Car):
        pass

    def test_passes_step_argument_to_interval_object(self, create_car):
        car = create_car([Decimal('0.2'), Decimal('0.8')])
        assert car.price_range.lower == Decimal('0')
        assert car.price_range.upper == Decimal('1')
        assert car.price_range.step == Decimal('0.5')

    def test_passes_step_fetched_objects(self, session, Car, create_car):
        create_car([Decimal('0.2'), Decimal('0.8')])
        session.expunge_all()
        car = session.query(Car).first()
        assert car.price_range.lower == Decimal('0')
        assert car.price_range.upper == Decimal('1')
        assert car.price_range.step == Decimal('0.5')
