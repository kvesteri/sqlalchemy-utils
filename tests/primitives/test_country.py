import operator

import pytest

from sqlalchemy_utils import Country, i18n


@pytest.fixture
def set_get_locale():
    i18n.get_locale = lambda: i18n.babel.Locale('en')


@pytest.mark.skipif('i18n.babel is None')
@pytest.mark.usefixtures('set_get_locale')
class TestCountry:

    def test_init(self):
        assert Country('FI') == Country(Country('FI'))

    def test_constructor_with_wrong_type(self):
        with pytest.raises(TypeError) as e:
            Country(None)
        assert str(e.value) == (
            "Country() argument must be a string or a country, not 'NoneType'"
        )

    def test_constructor_with_invalid_code(self):
        with pytest.raises(ValueError) as e:
            Country('SomeUnknownCode')
        assert str(e.value) == (
            'Could not convert string to country code: SomeUnknownCode'
        )

    @pytest.mark.parametrize(
        'code',
        (
            'FI',
            'US',
        )
    )
    def test_validate_with_valid_codes(self, code):
        Country.validate(code)

    def test_validate_with_invalid_code(self):
        with pytest.raises(ValueError) as e:
            Country.validate('SomeUnknownCode')
        assert str(e.value) == (
            'Could not convert string to country code: SomeUnknownCode'
        )

    def test_equality_operator(self):
        assert Country('FI') == 'FI'
        assert 'FI' == Country('FI')
        assert Country('FI') == Country('FI')

    def test_non_equality_operator(self):
        assert Country('FI') != 'sv'
        assert not (Country('FI') != 'FI')

    @pytest.mark.parametrize(
        'op, code_left, code_right, is_',
        [
            (operator.lt, 'ES', 'FI', True),
            (operator.lt, 'FI', 'ES', False),
            (operator.lt, 'ES', 'ES', False),

            (operator.le, 'ES', 'FI', True),
            (operator.le, 'FI', 'ES', False),
            (operator.le, 'ES', 'ES', True),

            (operator.ge, 'ES', 'FI', False),
            (operator.ge, 'FI', 'ES', True),
            (operator.ge, 'ES', 'ES', True),

            (operator.gt, 'ES', 'FI', False),
            (operator.gt, 'FI', 'ES', True),
            (operator.gt, 'ES', 'ES', False),
        ]
    )
    def test_ordering(self, op, code_left, code_right, is_):
        country_left = Country(code_left)
        country_right = Country(code_right)
        assert op(country_left, country_right) is is_
        assert op(country_left, code_right) is is_
        assert op(code_left, country_right) is is_

    def test_hash(self):
        assert hash(Country('FI')) == hash('FI')

    def test_repr(self):
        assert repr(Country('FI')) == "Country('FI')"

    def test_str(self):
        country = Country('FI')
        assert str(country) == 'Finland'
