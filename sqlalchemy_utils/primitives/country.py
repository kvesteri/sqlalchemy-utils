import six
from sqlalchemy_utils import i18n


class Country(object):
    def __init__(self, code_or_country):
        if isinstance(code_or_country, Country):
            self.code = code_or_country.code
        else:
            self.code = code_or_country

    @property
    def name(self):
        return i18n.get_locale().territories[self.code]

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
