from colour import Color
import sqlalchemy as sa
from sqlalchemy_utils import (
    ColorType,
    NumberRangeType,
    NumberRange,
    PhoneNumberType,
    PhoneNumber,
    coercion_listener
)
from tests import DatabaseTestCase


class TestCoercionListener(DatabaseTestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            fav_color = sa.Column(ColorType)
            phone_number = sa.Column(PhoneNumberType(country_code='FI'))
            number_of_friends = sa.Column(NumberRangeType)

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User
        sa.event.listen(
            sa.orm.mapper, 'mapper_configured', coercion_listener
        )

    def test_scalar_attributes_get_coerced_to_objects(self):
        user = self.User(
            fav_color='white',
            phone_number='050111222',
            number_of_friends='[12, 18]'
        )
        assert isinstance(user.fav_color, Color)
        assert isinstance(user.phone_number, PhoneNumber)
        assert isinstance(user.number_of_friends, NumberRange)
