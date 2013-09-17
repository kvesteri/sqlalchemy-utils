import sqlalchemy as sa
from sqlalchemy_utils import CountryType, Country, i18n
from tests import TestCase


def get_locale():
    class Locale():
        territories = {'fi': 'Finland'}

    return Locale()


i18n.get_locale = get_locale


class TestCountryType(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            country = sa.Column(CountryType)

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_color_parameter_processing(self):
        user = self.User(
            country=Country(u'fi')
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.country.name == u'Finland'

    def test_scalar_attributes_get_coerced_to_objects(self):
        user = self.User(country='fi')

        assert isinstance(user.country, Country)
