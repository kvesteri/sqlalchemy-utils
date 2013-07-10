import sqlalchemy as sa
from pytest import raises
from tests import TestCase
from sqlalchemy_utils import (
    NumberRangeType,
    NumberRange,
    NumberRangeException,
    coercion_listener
)


class TestNumberRangeType(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            persons_at_night = sa.Column(NumberRangeType)

            def __repr__(self):
                return 'Building(%r)' % self.id

        self.Building = Building
        sa.event.listen(sa.orm.mapper, 'mapper_configured', coercion_listener)

    def test_save_number_range(self):
        building = self.Building(
            persons_at_night=NumberRange(1, 3)
        )

        self.session.add(building)
        self.session.commit()
        building = self.session.query(self.Building).first()
        assert building.persons_at_night.min_value == 1
        assert building.persons_at_night.max_value == 3

    def test_nullify_number_range(self):
        building = self.Building(
            persons_at_night=NumberRange(1, 3)
        )

        self.session.add(building)
        self.session.commit()

        building = self.session.query(self.Building).first()
        building.persons_at_night = None
        self.session.commit()

        building = self.session.query(self.Building).first()
        assert building.persons_at_night is None

    def test_scalar_attributes_get_coerced_to_objects(self):
        building = self.Building(persons_at_night='[12, 18]')

        assert isinstance(building.persons_at_night, NumberRange)


class TestNumberRange(object):
    def test_equality_operator(self):
        assert NumberRange(1, 3) == NumberRange(1, 3)

    def test_str_representation(self):
        assert str(NumberRange(1, 3)) == '1 - 3'
        assert str(NumberRange(1, 1)) == '1'

    def test_raises_exception_for_badly_constructed_range(self):
        with raises(NumberRangeException):
            NumberRange(3, 2)

    def test_from_str_supports_single_integers(self):
        number_range = NumberRange.from_str('1')
        assert number_range.min_value == 1
        assert number_range.max_value == 1

    def test_from_str_exception_handling(self):
        with raises(NumberRangeException):
            NumberRange.from_str('1 - ')

    def test_from_normalized_str(self):
        assert str(NumberRange.from_normalized_str('[1,2]')) == '1 - 2'
        assert str(NumberRange.from_normalized_str('[1,3)')) == '1 - 2'
        assert str(NumberRange.from_normalized_str('(1,3)')) == '2'

    def test_add_operator(self):
        assert NumberRange(1, 2) + NumberRange(1, 2) == NumberRange(2, 4)

    def test_sub_operator(self):
        assert NumberRange(1, 3) - NumberRange(1, 2) == NumberRange(0, 1)
