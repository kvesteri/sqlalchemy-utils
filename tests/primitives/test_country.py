import pytest
import six

from sqlalchemy_utils import Country, i18n


@pytest.fixture
def set_get_locale():
    i18n.get_locale = lambda: i18n.babel.Locale('en')


@pytest.mark.skipif('i18n.babel is None')
@pytest.mark.usefixtures('set_get_locale')
class TestCountry(object):

    def test_init(self):
        assert Country(u'FI') == Country(Country(u'FI'))

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
        assert Country(u'FI') == u'FI'
        assert u'FI' == Country(u'FI')
        assert Country(u'FI') == Country(u'FI')

    def test_non_equality_operator(self):
        assert Country(u'FI') != u'sv'
        assert not (Country(u'FI') != u'FI')

    def test_hash(self):
        return hash(Country('FI')) == hash('FI')

    def test_repr(self):
        return repr(Country('FI')) == "Country('FI')"

    def test_unicode(self):
        country = Country('FI')
        assert six.text_type(country) == u'Finland'

    def test_str(self):
        country = Country('FI')
        assert str(country) == 'Finland'
