from pytest import mark, raises
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy_utils.types import money
from decimal import Decimal
from tests import TestCase


@mark.skipif('money.Money is None')
class TestMoneyType(TestCase):

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            
            cash = orm.composite(
                money.MoneyComposite,
                sa.Column('_cash_amount', sa.Float(asdecimal=True)),
                sa.Column('_cash_currency', sa.UnicodeText))

        self.User = User

    def test_processing(self):
        user = self.User()
        user.cash = money.MoneyComposite('10.2', 'USD')

        assert user._cash_amount == Decimal('10.2')
        assert user._cash_currency == 'USD'
