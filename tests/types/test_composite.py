import sqlalchemy as sa
from pytest import mark
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy_utils import (
    CompositeArray,
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
from tests import TestCase


class TestCompositeTypeWithRegularTypes(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Account(self.Base):
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

        self.Account = Account

    def test_parameter_processing(self):
        account = self.Account(
            balance=('USD', 15)
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15


@mark.skipif('i18n.babel is None')
class TestCompositeTypeWithTypeDecorators(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        i18n.get_locale = lambda: i18n.babel.Locale('en')

    def create_models(self):
        class Account(self.Base):
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

        self.Account = Account

    def test_result_set_processing(self):
        account = self.Account(
            balance=('USD', 15)
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balance.currency == Currency('USD')
        assert account.balance.amount == 15

    def test_parameter_processing(self):
        account = self.Account(
            balance=(Currency('USD'), 15)
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balance.currency == Currency('USD')
        assert account.balance.amount == 15


@mark.skipif('i18n.babel is None')
class TestCompositeTypeInsideArray(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def setup_method(self, method):
        self.type = CompositeType(
            'money_type',
            [
                sa.Column('currency', CurrencyType),
                sa.Column('amount', sa.Integer)
            ]
        )

        TestCase.setup_method(self, method)
        i18n.get_locale = lambda: i18n.babel.Locale('en')

    def create_models(self):
        class Account(self.Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            balances = sa.Column(
                CompositeArray(self.type)
            )

        self.Account = Account

    def test_parameter_processing(self):
        account = self.Account(
            balances=[
                self.type.type_cls(Currency('USD'), 15),
                self.type.type_cls(Currency('AUD'), 20)
            ]
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balances[0].currency == Currency('USD')
        assert account.balances[0].amount == 15
        assert account.balances[1].currency == Currency('AUD')
        assert account.balances[1].amount == 20


@mark.skipif('intervals is None')
class TestCompositeTypeWithRangeTypeInsideArray(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def setup_method(self, method):
        self.type = CompositeType(
            'category',
            [
                sa.Column('scale', NumericRangeType),
                sa.Column('name', sa.String)
            ]
        )

        TestCase.setup_method(self, method)

    def create_models(self):
        class Account(self.Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            categories = sa.Column(
                CompositeArray(self.type)
            )

        self.Account = Account

    def test_parameter_processing_with_named_tuple(self):
        account = self.Account(
            categories=[
                self.type.type_cls(
                    intervals.DecimalInterval([15, 18]),
                    'bad'
                ),
                self.type.type_cls(
                    intervals.DecimalInterval([18, 20]),
                    'good'
                )
            ]
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert (
            account.categories[0].scale == intervals.DecimalInterval([15, 18])
        )
        assert account.categories[0].name == 'bad'
        assert (
            account.categories[1].scale == intervals.DecimalInterval([18, 20])
        )
        assert account.categories[1].name == 'good'

    def test_parameter_processing_with_tuple(self):
        account = self.Account(
            categories=[
                (intervals.DecimalInterval([15, 18]), 'bad'),
                (intervals.DecimalInterval([18, 20]), 'good')
            ]
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert (
            account.categories[0].scale == intervals.DecimalInterval([15, 18])
        )
        assert account.categories[0].name == 'bad'
        assert (
            account.categories[1].scale == intervals.DecimalInterval([18, 20])
        )
        assert account.categories[1].name == 'good'

    def test_parameter_processing_with_nulls_as_composite_fields(self):
        account = self.Account(
            categories=[
                (None, 'bad'),
                (intervals.DecimalInterval([18, 20]), None)
            ]
        )
        self.session.add(account)
        self.session.commit()
        assert account.categories[0].scale is None
        assert account.categories[0].name == 'bad'
        assert (
            account.categories[1].scale == intervals.DecimalInterval([18, 20])
        )
        assert account.categories[1].name is None

    def test_parameter_processing_with_nulls_as_composites(self):
        account = self.Account(
            categories=[
                (None, None),
                None
            ]
        )
        self.session.add(account)
        self.session.commit()
        assert account.categories[0].scale is None
        assert account.categories[0].name is None
        assert account.categories[1] is None


class TestCompositeTypeWhenTypeAlreadyExistsInDatabase(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def setup_method(self, method):
        self.engine = create_engine(self.dns)
        self.engine.echo = True
        self.connection = self.engine.connect()
        self.Base = declarative_base()
        pg_composite.registered_composites = {}

        self.type = CompositeType(
            'money_type',
            [
                sa.Column('currency', sa.String),
                sa.Column('amount', sa.Integer)
            ]
        )

        self.create_models()
        sa.orm.configure_mappers()

        Session = sessionmaker(bind=self.connection)
        self.session = Session()
        self.session.execute(
            "CREATE TYPE money_type AS (currency VARCHAR, amount INTEGER)"
        )
        self.session.execute(
            """CREATE TABLE account (
                id SERIAL, balance MONEY_TYPE, PRIMARY KEY(id)
            )"""
        )
        register_composites(self.connection)

    def teardown_method(self, method):
        self.session.execute('DROP TABLE account')
        self.session.execute('DROP TYPE money_type')
        self.session.commit()
        self.session.close_all()
        self.connection.close()
        remove_composite_listeners()
        self.engine.dispose()

    def create_models(self):
        class Account(self.Base):
            __tablename__ = 'account'
            id = sa.Column(sa.Integer, primary_key=True)
            balance = sa.Column(self.type)

        self.Account = Account

    def test_parameter_processing(self):
        account = self.Account(
            balance=('USD', 15),
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15
