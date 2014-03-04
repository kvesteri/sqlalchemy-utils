from decimal import Decimal


from pytest import mark
import sqlalchemy as sa
intervals = None
try:
    import intervals
except ImportError:
    pass
from tests import TestCase
from infinity import inf
from sqlalchemy_utils import NumericRangeType


@mark.skipif('intervals is None')
class NumericRangeTestCase(TestCase):
    def create_models(self):
        class Car(self.Base):
            __tablename__ = 'car'
            id = sa.Column(sa.Integer, primary_key=True)
            price_range = sa.Column(NumericRangeType)

        self.Car = Car

    def create_car(self, number_range):
        car = self.Car(
            price_range=number_range
        )

        self.session.add(car)
        self.session.commit()
        return self.session.query(self.Car).first()

    def test_nullify_range(self):
        car = self.create_car(None)
        assert car.price_range is None

    @mark.parametrize(
        'number_range',
        (
            [1, 3],
            '1 - 3',
        )
    )
    def test_save_number_range(self, number_range):
        car = self.create_car(number_range)
        assert car.price_range.lower == 1
        assert car.price_range.upper == 3

    def test_infinite_upper_bound(self):
        car = self.create_car([1, inf])
        assert car.price_range.lower == 1
        assert car.price_range.upper == inf

    def test_infinite_lower_bound(self):
        car = self.create_car([-inf, 1])
        assert car.price_range.lower == -inf
        assert car.price_range.upper == 1

    def test_nullify_number_range(self):
        car = self.Car(
            price_range=intervals.IntInterval([1, 3])
        )

        self.session.add(car)
        self.session.commit()

        car = self.session.query(self.Car).first()
        car.price_range = None
        self.session.commit()

        car = self.session.query(self.Car).first()
        assert car.price_range is None

    def test_string_coercion(self):
        car = self.Car(price_range='[12, 18]')
        assert isinstance(car.price_range, intervals.DecimalInterval)

    def test_integer_coercion(self):
        car = self.Car(price_range=15)
        assert car.price_range.lower == 15
        assert car.price_range.upper == 15


class TestNumericRangeOnPostgres(NumericRangeTestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'


@mark.skipif('intervals is None')
class TestNumericRangeWithStep(TestCase):
    def create_models(self):
        class Car(self.Base):
            __tablename__ = 'car'
            id = sa.Column(sa.Integer, primary_key=True)
            price_range = sa.Column(NumericRangeType(step=Decimal('0.5')))

        self.Car = Car

    def create_car(self, number_range):
        car = self.Car(
            price_range=number_range
        )

        self.session.add(car)
        self.session.commit()
        return self.session.query(self.Car).first()

    def test_passes_step_argument_to_interval_object(self):
        car = self.create_car([Decimal('0.2'), Decimal('0.8')])
        assert car.price_range.lower == Decimal('0')
        assert car.price_range.upper == Decimal('1')
        assert car.price_range.step == Decimal('0.5')

    def test_passes_step_fetched_objects(self):
        self.create_car([Decimal('0.2'), Decimal('0.8')])
        self.session.expunge_all()
        car = self.session.query(self.Car).first()
        assert car.price_range.lower == Decimal('0')
        assert car.price_range.upper == Decimal('1')
        assert car.price_range.step == Decimal('0.5')
