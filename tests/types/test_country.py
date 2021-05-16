import pytest
import sqlalchemy as sa

from sqlalchemy_utils import Country, CountryType, i18n  # noqa


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        country = sa.Column(CountryType)

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('i18n.babel is None')
class TestCountryType(object):

    def test_parameter_processing(self, session, User):
        user = User(
            country=Country(u'FI')
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.country.name == u'Finland'

    def test_scalar_attributes_get_coerced_to_objects(self, User):
        user = User(country='FI')
        assert isinstance(user.country, Country)

    def test_literal_param(self, session, User):
        clause = User.country == 'FI'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == '"user".country = \'FI\''

    def test_compilation(self, User, session):
        query = sa.select([User.country])
        # the type should be cacheable and not throw exception
        session.execute(query)
