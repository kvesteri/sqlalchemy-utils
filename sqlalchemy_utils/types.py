import phonenumbers
from colour import Color
from functools import wraps
import sqlalchemy as sa
from sqlalchemy.orm.collections import InstrumentedList as _InstrumentedList
from sqlalchemy import types
from .operators import CaseInsensitiveComparator


class PhoneNumber(phonenumbers.phonenumber.PhoneNumber):
    '''
    Extends a PhoneNumber class from `Python phonenumbers library`_. Adds
    different phone number formats to attributes, so they can be easily used
    in templates. Phone number validation method is also implemented.

    Takes the raw phone number and country code as params and parses them
    into a PhoneNumber object.

    .. _Python phonenumbers library:
       https://github.com/daviddrysdale/python-phonenumbers

    :param raw_number:
        String representation of the phone number.
    :param country_code:
        Country code of the phone number.
    '''
    def __init__(self, raw_number, country_code=None):
        self._phone_number = phonenumbers.parse(raw_number, country_code)
        super(PhoneNumber, self).__init__(
            country_code=self._phone_number.country_code,
            national_number=self._phone_number.national_number,
            extension=self._phone_number.extension,
            italian_leading_zero=self._phone_number.italian_leading_zero,
            raw_input=self._phone_number.raw_input,
            country_code_source=self._phone_number.country_code_source,
            preferred_domestic_carrier_code=
            self._phone_number.preferred_domestic_carrier_code
        )
        self.national = phonenumbers.format_number(
            self._phone_number,
            phonenumbers.PhoneNumberFormat.NATIONAL
        )
        self.international = phonenumbers.format_number(
            self._phone_number,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        self.e164 = phonenumbers.format_number(
            self._phone_number,
            phonenumbers.PhoneNumberFormat.E164
        )

    def is_valid_number(self):
        return phonenumbers.is_valid_number(self._phone_number)

    def __unicode__(self):
        return self.national

    def __str__(self):
        return unicode(self).encode('utf-8')


class PhoneNumberType(types.TypeDecorator):
    """
    Changes PhoneNumber objects to a string representation on the way in and
    changes them back to PhoneNumber objects on the way out. If E164 is used
    as storing format, no country code is needed for parsing the database
    value to PhoneNumber object.
    """
    STORE_FORMAT = 'e164'
    impl = types.Unicode(20)

    def __init__(self, country_code='US', max_length=20, *args, **kwargs):
        super(PhoneNumberType, self).__init__(*args, **kwargs)
        self.country_code = country_code
        self.impl = types.Unicode(max_length)

    def process_bind_param(self, value, dialect):
        if value:
            return getattr(value, self.STORE_FORMAT)
        return value

    def process_result_value(self, value, dialect):
        if value:
            return PhoneNumber(value, self.country_code)
        return value

    def coercion_listener(self, target, value, oldvalue, initiator):
        if value is not None and not isinstance(value, PhoneNumber):
            value = PhoneNumber(value, country_code=self.country_code)
        return value


class ColorType(types.TypeDecorator):
    """
    Changes Color objects to a string representation on the way in and
    changes them back to Color objects on the way out.
    """
    STORE_FORMAT = 'hex'
    impl = types.Unicode(20)

    def __init__(self, max_length=20, *args, **kwargs):
        super(ColorType, self).__init__(*args, **kwargs)
        self.impl = types.Unicode(max_length)

    def process_bind_param(self, value, dialect):
        if value:
            return getattr(value, self.STORE_FORMAT)
        return value

    def process_result_value(self, value, dialect):
        if value:
            return Color(value)
        return value

    def coercion_listener(self, target, value, oldvalue, initiator):
        if value is not None and not isinstance(value, Color):
            value = Color(value)
        return value


class ScalarListException(Exception):
    pass


class ScalarListType(types.TypeDecorator):
    impl = sa.UnicodeText()

    def __init__(self, coerce_func=unicode, separator=u','):
        self.separator = unicode(separator)
        self.coerce_func = coerce_func

    def process_bind_param(self, value, dialect):
        # Convert list of values to unicode separator-separated list
        # Example: [1, 2, 3, 4] -> u'1, 2, 3, 4'
        if value is not None:
            if any(self.separator in unicode(item) for item in value):
                raise ScalarListException(
                    "List values can't contain string '%s' (its being used as "
                    "separator. If you wish for scalar list values to contain "
                    "these strings, use a different separator string."
                )
            return self.separator.join(
                map(unicode, value)
            )

    def process_result_value(self, value, dialect):
        if value is not None:
            if value == u'':
                return []
            # coerce each value
            return map(
                self.coerce_func, value.split(self.separator)
            )


class EmailType(sa.types.TypeDecorator):
    impl = sa.Unicode(255)
    comparator_factory = CaseInsensitiveComparator

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.lower()
        return value


class NumberRangeRawType(types.UserDefinedType):
    """
    Raw number range type, only supports PostgreSQL for now.
    """
    def get_col_spec(self):
        return 'int4range'


class NumberRangeType(types.TypeDecorator):
    impl = NumberRangeRawType

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.normalized
        return value

    def process_result_value(self, value, dialect):
        if value:
            if not isinstance(value, basestring):
                value = NumberRange.from_range_object(value)
            else:
                return NumberRange.from_normalized_str(value)
        return value

    def coercion_listener(self, target, value, oldvalue, initiator):
        if value is not None and not isinstance(value, NumberRange):
            if isinstance(value, basestring):
                value = NumberRange.from_normalized_str(value)
            else:
                raise TypeError
        return value


class NumberRangeException(Exception):
    pass


class RangeBoundsException(NumberRangeException):
    def __init__(self, min_value, max_value):
        self.message = 'Min value %d is bigger than max value %d.' % (
            min_value,
            max_value
        )


class NumberRange(object):
    def __init__(self, min_value, max_value):
        if min_value > max_value:
            raise RangeBoundsException(min_value, max_value)
        self.min_value = min_value
        self.max_value = max_value

    @classmethod
    def from_range_object(cls, value):
        min_value = value.lower
        max_value = value.upper
        if not value.lower_inc:
            min_value += 1

        if not value.upper_inc:
            max_value -= 1

        return cls(min_value, max_value)

    @classmethod
    def from_normalized_str(cls, value):
        """
        Returns new NumberRange object from normalized number range format.

        Example ::

            range = NumberRange.from_normalized_str('[23, 45]')
            range.min_value = 23
            range.max_value = 45

            range = NumberRange.from_normalized_str('(23, 45]')
            range.min_value = 24
            range.max_value = 45

            range = NumberRange.from_normalized_str('(23, 45)')
            range.min_value = 24
            range.max_value = 44
        """
        if value is not None:
            values = value[1:-1].split(',')
            try:
                min_value, max_value = map(
                    lambda a: int(a.strip()), values
                )
            except ValueError, e:
                raise NumberRangeException(e.message)

            if value[0] == '(':
                min_value += 1

            if value[-1] == ')':
                max_value -= 1

            return cls(min_value, max_value)

    @classmethod
    def from_str(cls, value):
        if value is not None:
            values = value.split('-')
            if len(values) == 1:
                min_value = max_value = int(value.strip())
            else:
                try:
                    min_value, max_value = map(
                        lambda a: int(a.strip()), values
                    )
                except ValueError, e:
                    raise NumberRangeException(e.message)
            return cls(min_value, max_value)

    @property
    def normalized(self):
        return '[%s, %s]' % (self.min_value, self.max_value)

    def __eq__(self, other):
        try:
            return (
                self.min_value == other.min_value and
                self.max_value == other.max_value
            )
        except AttributeError:
            return NotImplemented

    def __repr__(self):
        return 'NumberRange(%r, %r)' % (self.min_value, self.max_value)

    def __str__(self):
        if self.min_value != self.max_value:
            return '%s - %s' % (self.min_value, self.max_value)
        return str(self.min_value)

    def __add__(self, other):
        try:
            return NumberRange(
                self.min_value + other.min_value,
                self.max_value + other.max_value
            )
        except AttributeError:
            return NotImplemented

    def __iadd__(self, other):
        try:
            self.min_value += other.min_value
            self.max_value += other.max_value
            return self
        except AttributeError:
            return NotImplemented

    def __sub__(self, other):
        try:
            return NumberRange(
                self.min_value - other.min_value,
                self.max_value - other.max_value
            )
        except AttributeError:
            return NotImplemented

    def __isub__(self, other):
        try:
            self.min_value -= other.min_value
            self.max_value -= other.max_value
            return self
        except AttributeError:
            return NotImplemented


class InstrumentedList(_InstrumentedList):
    """Enhanced version of SQLAlchemy InstrumentedList. Provides some
    additional functionality."""

    def any(self, attr):
        return any(getattr(item, attr) for item in self)

    def all(self, attr):
        return all(getattr(item, attr) for item in self)


def instrumented_list(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return InstrumentedList([item for item in f(*args, **kwargs)])
    return wrapper
