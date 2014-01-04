import sqlalchemy as sa
from tests import TestCase
from sqlalchemy_utils import (
    NumberRangeType,
    NumberRange,
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

    def test_save_number_range(self):
        building = self.Building(
            persons_at_night=NumberRange(1, 3)
        )

        self.session.add(building)
        self.session.commit()
        building = self.session.query(self.Building).first()
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper == 3

    def test_infinite_upper_bound(self):
        building = self.Building(
            persons_at_night=NumberRange(1, float('inf'))
        )
        self.session.add(building)
        self.session.commit()
        building = self.session.query(self.Building).first()
        assert building.persons_at_night.lower == 1
        assert building.persons_at_night.upper is None

    def test_infinite_lower_bound(self):
        building = self.Building(
            persons_at_night=NumberRange(-float('inf'), 1)
        )
        self.session.add(building)
        self.session.commit()
        building = self.session.query(self.Building).first()
        assert building.persons_at_night.lower is None
        assert building.persons_at_night.upper is 1

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

    def test_string_coercion(self):
        building = self.Building(persons_at_night='[12, 18]')

        assert isinstance(building.persons_at_night, NumberRange)

    def test_integer_coercion(self):
        building = self.Building(persons_at_night=15)
        assert building.persons_at_night.lower == 15
        assert building.persons_at_night.upper == 15
