import six
from sqlalchemy_utils import i18n
from sqlalchemy_utils.utils import str_coercible


@str_coercible
class Country(object):
    def __init__(self, code_or_country):
        if isinstance(code_or_country, Country):
            self.code = code_or_country.code
        elif isinstance(code_or_country, six.string_types):
            self.validate(code_or_country)
            self.code = code_or_country
        else:
            raise TypeError(
                "Country() argument must be a string or a country, not '{0}'"
                .format(
                    type(code_or_country).__name__
                )
            )

    @property
    def name(self):
        return i18n.get_locale().territories[self.code]

    @classmethod
    def validate(self, code):
        try:
            i18n.get_locale().territories[code]
        except KeyError:
            raise ValueError(
                'Could not convert string to country code: {0}'.format(code)
            )

    def __eq__(self, other):
        if isinstance(other, Country):
            return self.code == other.code
        elif isinstance(other, six.string_types):
            return self.code == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.code)

    def __unicode__(self):
        return self.name
