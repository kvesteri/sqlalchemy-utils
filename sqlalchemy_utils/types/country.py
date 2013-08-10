from sqlalchemy import types
from sqlalchemy_utils import ImproperlyConfigured


class Country(object):
    get_locale = None

    def __init__(self, code):
        self.code = code
        if self.get_locale is None:
            ImproperlyConfigured(
                "Country class needs define get_locale."
            )

    @property
    def name(self):
        return self.get_locale().territories[self.code]

    def __eq__(self, other):
        if isinstance(other, Country):
            return self.code == other.code
        else:
            return NotImplemented

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.code)

    def __unicode__(self):
        return self.name


class CountryType(types.TypeDecorator):
    impl = types.String(2)

    def process_bind_param(self, value, dialect):
        if isinstance(value, Country):
            return value.code

        if isinstance(value, basestring):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return Country(value)
