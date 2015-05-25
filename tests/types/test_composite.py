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
    register_composites,
    remove_composite_listeners
)
from sqlalchemy_utils.types.currency import babel
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


@mark.skipif('babel is None')
class TestCompositeTypeWithTypeDecorators(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        i18n.get_locale = lambda: babel.Locale('en')

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

    def test_parameter_processing(self):
        account = self.Account(
            balance=('USD', 15)
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balance.currency == Currency('USD')
        assert account.balance.amount == 15


@mark.skipif('babel is None')
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
        i18n.get_locale = lambda: babel.Locale('en')

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
                self.type.type_cls('USD', 15),
                self.type.type_cls('AUD', 20)
            ]
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balances[0].currency == Currency('USD')
        assert account.balances[0].amount == 15
        assert account.balances[1].currency == Currency('AUD')
        assert account.balances[1].amount == 20


class TestCompositeTypeWhenTypeAlreadyExistsInDatabase(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def setup_method(self, method):
        self.engine = create_engine(self.dns)
        # self.engine.echo = True
        self.connection = self.engine.connect()
        self.Base = declarative_base()

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
        self.session.close_all()
        self.connection.close()
        remove_composite_listeners()
        self.engine.dispose()

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
            balance=('USD', 15),
        )

        self.session.add(account)
        self.session.commit()

        account = self.session.query(self.Account).first()
        assert account.balance.currency == 'USD'
        assert account.balance.amount == 15
