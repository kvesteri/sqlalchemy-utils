import sqlalchemy as sa
from pytest import mark

from sqlalchemy_utils import Country, CountryType, i18n  # noqa
from tests import TestCase


@mark.skipif('i18n.babel is None')
class TestCountryType(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            country = sa.Column(CountryType)

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_parameter_processing(self):
        user = self.User(
            country=Country(u'FI')
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.country.name == u'Finland'

    def test_scalar_attributes_get_coerced_to_objects(self):
        user = self.User(country='FI')
        assert isinstance(user.country, Country)
