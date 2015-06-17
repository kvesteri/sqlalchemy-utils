# -*- coding: utf-8 -*-
import six
from pytest import mark, raises

from sqlalchemy_utils import Currency, i18n


@mark.skipif('i18n.babel is None')
class TestCurrency(object):
    def setup_method(self, method):
        i18n.get_locale = lambda: i18n.babel.Locale('en')

    def test_init(self):
        assert Currency('USD') == Currency(Currency('USD'))

    def test_hashability(self):
        assert len(set([Currency('USD'), Currency('USD')])) == 1

    def test_invalid_currency_code(self):
        with raises(ValueError):
            Currency('Unknown code')

    def test_invalid_currency_code_type(self):
        with raises(TypeError):
            Currency(None)

    @mark.parametrize(
        ('code', 'name'),
        (
            ('USD', 'US Dollar'),
            ('EUR', 'Euro')
        )
    )
    def test_name_property(self, code, name):
        assert Currency(code).name == name

    @mark.parametrize(
        ('code', 'symbol'),
        (
            ('USD', u'$'),
            ('EUR', u'€')
        )
    )
    def test_symbol_property(self, code, symbol):
        assert Currency(code).symbol == symbol

    def test_equality_operator(self):
        assert Currency('USD') == 'USD'
        assert 'USD' == Currency('USD')
        assert Currency('USD') == Currency('USD')

    def test_non_equality_operator(self):
        assert Currency('USD') != 'EUR'
        assert not (Currency('USD') != 'USD')

    def test_unicode(self):
        currency = Currency('USD')
        assert six.text_type(currency) == u'USD'

    def test_str(self):
        currency = Currency('USD')
        assert str(currency) == 'USD'

    def test_representation(self):
        currency = Currency('USD')
        assert repr(currency) == "Currency('USD')"
