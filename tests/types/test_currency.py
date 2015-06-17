# -*- coding: utf-8 -*-
import sqlalchemy as sa
from pytest import mark

from sqlalchemy_utils import Currency, CurrencyType, i18n
from tests import TestCase


@mark.skipif('i18n.babel is None')
class TestCurrencyType(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        i18n.get_locale = lambda: i18n.babel.Locale('en')

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            currency = sa.Column(CurrencyType)

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_parameter_processing(self):
        user = self.User(
            currency=Currency('USD')
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.currency.name == u'US Dollar'

    def test_scalar_attributes_get_coerced_to_objects(self):
        user = self.User(currency='USD')
        assert isinstance(user.currency, Currency)
