import pytest
import sqlalchemy as sa

from sqlalchemy_utils import Currency, CurrencyType, i18n
from sqlalchemy_utils.compat import _select_args


@pytest.fixture
def set_get_locale():
    i18n.get_locale = lambda: i18n.babel.Locale('en')


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        currency = sa.Column(CurrencyType)

        def __repr__(self):
            return 'User(%r)' % self.id

    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('i18n.babel is None')
class TestCurrencyType:
    def test_parameter_processing(self, session, User, set_get_locale):
        user = User(
            currency=Currency('USD')
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.currency.name == 'US Dollar'

    def test_scalar_attributes_get_coerced_to_objects(
        self,
        User,
        set_get_locale
    ):
        user = User(currency='USD')
        assert isinstance(user.currency, Currency)

    def test_literal_param(self, session, User):
        clause = User.currency == 'USD'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == '"user".currency = \'USD\''

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.currency))
        # the type should be cacheable and not throw exception
        session.execute(query)
