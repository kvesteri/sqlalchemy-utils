import six
from sqlalchemy import types


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
            if not isinstance(value, six.string_types):
                value = NumberRange.from_range_object(value)
            else:
                return NumberRange.from_normalized_str(value)
        return value

    def coercion_listener(self, target, value, oldvalue, initiator):
        if value is not None and not isinstance(value, NumberRange):
            if isinstance(value, six.string_types):
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
            except ValueError as e:
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
                except ValueError as e:
                    raise NumberRangeException(str(e))
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
