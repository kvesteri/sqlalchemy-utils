import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import close_all_sessions

from sqlalchemy_utils import (
    CompositeType,
    Currency,
    CurrencyType,
    i18n,
    NumericRangeType,
    register_composites,
    remove_composite_listeners
)
from sqlalchemy_utils.types import pg_composite
from sqlalchemy_utils.types.range import intervals


@pytest.mark.usefixtures('postgresql_dsn')
class TestCompositeTypeWithRegularTypes:

    @pytest.fixture
    def Account(self, Base):
        class Account(Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            balance = sa.Column(
                CompositeType(
                    'money_type',
                    [
                        sa.Column('currency', sa.String),
                        sa.Column('amount', sa.Integer)
                    ]
                )
            )

        return Account

    @pytest.fixture
    def init_models(self, Account):
        pass

    def test_parameter_processing(self, session, Account):
        account = Account(
            balance=('USD', 15)
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15

    def test_non_ascii_chars(self, session, Account):
        account = Account(
            balance=('ääöö', 15)
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == 'ääöö'
        assert account.balance.amount == 15

    def test_dict_input(self, session, Account):
        account = Account(
            balance={'currency': 'USD', 'amount': 15}
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15

    def test_incomplete_dict(self, session, Account):
        """
        Postgres doesn't allow non-nullabe fields in Composite Types:

        "no constraints (such as NOT NULL) can presently be included"
        (https://www.postgresql.org/docs/10/rowtypes.html)

        So this should be allowed.
        """

        account = Account(
            balance={'amount': 15}
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency is None
        assert account.balance.amount == 15


@pytest.mark.skipif('i18n.babel is None')
@pytest.mark.usefixtures('postgresql_dsn')
class TestCompositeTypeWithTypeDecorators:

    @pytest.fixture
    def Account(self, Base):
        class Account(Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            balance = sa.Column(
                CompositeType(
                    'money_type',
                    [
                        sa.Column('currency', CurrencyType),
                        sa.Column('amount', sa.Integer)
                    ]
                )
            )

        return Account

    @pytest.fixture
    def init_models(self, Account):
        i18n.get_locale = lambda: i18n.babel.Locale('en')

    def test_result_set_processing(self, session, Account):
        account = Account(
            balance=('USD', 15)
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == Currency('USD')
        assert account.balance.amount == 15

    def test_parameter_processing(self, session, Account):
        account = Account(
            balance=(Currency('USD'), 15)
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == Currency('USD')
        assert account.balance.amount == 15

    def test_dict_input(self, session, Account):
        account = Account(
            balance={'currency': Currency('USD'), 'amount': 15}
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15


@pytest.mark.skipif('i18n.babel is None')
@pytest.mark.usefixtures('postgresql_dsn')
class TestCompositeTypeInsideArray:

    @pytest.fixture
    def type_(self):
        return CompositeType(
            'money_type',
            [
                sa.Column('currency', CurrencyType),
                sa.Column('amount', sa.Integer)
            ]
        )

    @pytest.fixture
    def Account(self, Base, type_):
        class Account(Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            balances = sa.Column(
                ARRAY(type_, dimensions=1)
            )

        return Account

    @pytest.fixture
    def init_models(self, Account):
        i18n.get_locale = lambda: i18n.babel.Locale('en')

    def test_parameter_processing(self, session, type_, Account):
        account = Account(
            balances=[
                type_.type_cls(Currency('USD'), 15),
                type_.type_cls(Currency('AUD'), 20)
            ]
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balances[0].currency == Currency('USD')
        assert account.balances[0].amount == 15
        assert account.balances[1].currency == Currency('AUD')
        assert account.balances[1].amount == 20

    def test_dict_input(self, session, type_, Account):
        account = Account(
            balances=[
                {'currency': Currency('USD'), 'amount': 15},
                {'currency': Currency('AUD'), 'amount': 20}
            ]
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balances[0].currency == Currency('USD')
        assert account.balances[0].amount == 15
        assert account.balances[1].currency == Currency('AUD')
        assert account.balances[1].amount == 20


@pytest.mark.skipif('intervals is None')
@pytest.mark.usefixtures('postgresql_dsn')
class TestCompositeTypeWithRangeTypeInsideArray:

    @pytest.fixture
    def type_(self):
        return CompositeType(
            'category',
            [
                sa.Column('scale', NumericRangeType),
                sa.Column('name', sa.String)
            ]
        )

    @pytest.fixture
    def Account(self, Base, type_):
        class Account(Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            categories = sa.Column(
                ARRAY(type_, dimensions=1)
            )

        return Account

    @pytest.fixture
    def init_models(self, Account):
        pass

    def test_parameter_processing_with_named_tuple(
        self,
        session,
        type_,
        Account
    ):
        account = Account(
            categories=[
                type_.type_cls(
                    intervals.DecimalInterval([15, 18]),
                    'bad'
                ),
                type_.type_cls(
                    intervals.DecimalInterval([18, 20]),
                    'good'
                )
            ]
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert (
            account.categories[0].scale == intervals.DecimalInterval([15, 18])
        )
        assert account.categories[0].name == 'bad'
        assert (
            account.categories[1].scale == intervals.DecimalInterval([18, 20])
        )
        assert account.categories[1].name == 'good'

    def test_parameter_processing_with_tuple(self, session, Account):
        account = Account(
            categories=[
                (intervals.DecimalInterval([15, 18]), 'bad'),
                (intervals.DecimalInterval([18, 20]), 'good')
            ]
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert (
            account.categories[0].scale == intervals.DecimalInterval([15, 18])
        )
        assert account.categories[0].name == 'bad'
        assert (
            account.categories[1].scale == intervals.DecimalInterval([18, 20])
        )
        assert account.categories[1].name == 'good'

    def test_parameter_processing_with_nulls_as_composite_fields(
        self,
        session,
        Account
    ):
        account = Account(
            categories=[
                (None, 'bad'),
                (intervals.DecimalInterval([18, 20]), None)
            ]
        )
        session.add(account)
        session.commit()
        assert account.categories[0].scale is None
        assert account.categories[0].name == 'bad'
        assert (
            account.categories[1].scale == intervals.DecimalInterval([18, 20])
        )
        assert account.categories[1].name is None

    def test_parameter_processing_with_nulls_as_composites(
        self,
        session,
        Account
    ):
        account = Account(
            categories=[
                (None, None),
                None
            ]
        )
        session.add(account)
        session.commit()
        assert account.categories[0].scale is None
        assert account.categories[0].name is None
        assert account.categories[1] is None


@pytest.mark.usefixtures('postgresql_dsn')
class TestCompositeTypeWhenTypeAlreadyExistsInDatabase:

    @pytest.fixture
    def Account(self, Base):
        pg_composite.registered_composites = {}

        type_ = CompositeType(
            'money_type',
            [
                sa.Column('currency', sa.String),
                sa.Column('amount', sa.Integer)
            ]
        )

        class Account(Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            balance = sa.Column(type_)

        return Account

    @pytest.fixture
    def session(self, request, engine, connection, Base, Account):
        sa.orm.configure_mappers()

        Session = sessionmaker(bind=connection)
        session = Session()
        session.execute(
            sa.text("CREATE TYPE money_type AS (currency VARCHAR, amount INTEGER)")
        )
        session.execute(
            sa.text("""CREATE TABLE account (
                id SERIAL, balance MONEY_TYPE, PRIMARY KEY(id)
            )""")
        )

        def teardown():
            session.execute(sa.text('DROP TABLE account'))
            session.execute(sa.text('DROP TYPE money_type'))
            session.commit()
            close_all_sessions()
            connection.close()
            remove_composite_listeners()
            engine.dispose()

        register_composites(connection)
        request.addfinalizer(teardown)

        return session

    def test_parameter_processing(self, session, Account):
        account = Account(
            balance=('USD', 15),
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15


@pytest.mark.usefixtures('postgresql_dsn')
class TestCompositeTypeWithMixedCase:

    @pytest.fixture
    def Account(self, Base):
        pg_composite.registered_composites = {}

        type_ = CompositeType(
            'MoneyType',
            [
                sa.Column('currency', sa.String),
                sa.Column('amount', sa.Integer)
            ]
        )

        class Account(Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            balance = sa.Column(type_)

        return Account

    @pytest.fixture
    def session(self, request, engine, connection, Base, Account):
        sa.orm.configure_mappers()

        Session = sessionmaker(bind=connection)
        try:
            # Enable sqlalchemy 2.0 behavior
            session = Session(future=True)
        except TypeError:
            # sqlalchemy 1.3
            session = Session()
        session.execute(
            sa.text('CREATE TYPE "MoneyType" AS (currency VARCHAR, amount INTEGER)')
        )
        session.execute(sa.text(
            """CREATE TABLE account (
                id SERIAL, balance "MoneyType", PRIMARY KEY(id)
            )"""
        ))

        def teardown():
            session.execute(sa.text('DROP TABLE account'))
            session.execute(sa.text('DROP TYPE "MoneyType"'))
            session.commit()
            close_all_sessions()
            connection.close()
            remove_composite_listeners()
            engine.dispose()

        register_composites(connection)
        request.addfinalizer(teardown)

        return session

    def test_parameter_processing(self, session, Account):
        account = Account(
            balance=('USD', 15),
        )

        session.add(account)
        session.commit()

        account = session.query(Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15
