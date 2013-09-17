from sqlalchemy import types
import six
from .scalar_coercible import ScalarCoercible
from sqlalchemy_utils import i18n


class Country(object):
    def __init__(self, code):
        self.code = code

    @property
    def name(self):
        return i18n.get_locale().territories[self.code]

    def __eq__(self, other):
        if isinstance(other, Country):
            return self.code == other.code
        else:
            return NotImplemented

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.code)

    def __unicode__(self):
        return self.name


class CountryType(types.TypeDecorator, ScalarCoercible):
    """
    Changes Country objects to a string representation on the way in and
    changes them back to Country objects on the way out.
    """

    impl = types.String(2)

    def process_bind_param(self, value, dialect):
        if isinstance(value, Country):
            return value.code

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return Country(value)

    def _coerce(self, value):
        if value is not None and not isinstance(value, Country):
            return Country(value)
        return value
