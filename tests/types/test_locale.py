import pytest
import sqlalchemy as sa

from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.types import locale


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        locale = sa.Column(locale.LocaleType)

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('locale.babel is None')
class TestLocaleType:
    def test_parameter_processing(self, session, User):
        user = User(
            locale=locale.babel.Locale('fi')
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()

    def test_territory_parsing(self, session, User):
        ko_kr = locale.babel.Locale('ko', territory='KR')
        user = User(locale=ko_kr)
        session.add(user)
        session.commit()

        assert session.query(User.locale).first()[0] == ko_kr

    def test_coerce_territory_parsing(self, User):
        user = User()
        user.locale = 'ko_KR'
        assert user.locale == locale.babel.Locale('ko', territory='KR')

    def test_scalar_attributes_get_coerced_to_objects(self, User):
        user = User(locale='en_US')

        assert isinstance(user.locale, locale.babel.Locale)

    def test_unknown_locale_throws_exception(self, User):
        with pytest.raises(locale.babel.UnknownLocaleError):
            User(locale='unknown')

    def test_literal_param(self, session, User):
        clause = User.locale == 'en_US'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == '"user".locale = \'en_US\''

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.locale))

        # the type should be cacheable and not throw exception
        session.execute(query)
