intervals = None
try:
    import intervals
except ImportError:
    pass
import six
import sqlalchemy as sa
from sqlalchemy import types
from ..exceptions import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible


class INT4RANGE(types.UserDefinedType):
    """
    Raw number range type, only supports PostgreSQL for now.
    """
    def get_col_spec(self):
        return 'int4range'


class INT8RANGE(types.UserDefinedType):
    def get_col_spec(self):
        return 'int8range'


class NUMRANGE(types.UserDefinedType):
    def get_col_spec(self):
        return 'numrange'


class DATERANGE(types.UserDefinedType):
    def get_col_spec(self):
        return 'daterange'


class TSRANGE(types.UserDefinedType):
    def get_col_spec(self):
        return 'tsrange'


class TSTZRANGE(types.UserDefinedType):
    def get_col_spec(self):
        return 'tstzrange'


class RangeComparator(types.TypeEngine.Comparator):
    @classmethod
    def coerce_arg(cls, func):
        def operation(self, other, **kwargs):
            coerced_types = (
                self.type.interval_class.type,
                tuple,
                list,
            ) + six.string_types

            if isinstance(other, coerced_types):
                other = self.type.interval_class(other)
            return getattr(types.TypeEngine.Comparator, func)(
                self, other, **kwargs
            )
        return operation


funcs = [
    '__eq__',
    '__ne__',
    '__lt__',
    '__le__',
    '__gt__',
    '__ge__',
]


for func in funcs:
    setattr(
        RangeComparator,
        func,
        RangeComparator.coerce_arg(func)
    )


class RangeType(types.TypeDecorator, ScalarCoercible):
    comparator_factory = RangeComparator

    def __init__(self, *args, **kwargs):
        if intervals is None:
            raise ImproperlyConfigured(
                'RangeType needs intervals package installed.'
            )
        super(RangeType, self).__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use the native JSON type.
            return dialect.type_descriptor(self.impl)
        else:
            return dialect.type_descriptor(sa.String(255))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value:
            return self.canonicalize_result_value(
                self.interval_class(value)
            )
        return value

    def canonicalize_result_value(self, value):
        return intervals.canonicalize(value, True, True)

    def _coerce(self, value):
        if value is not None:
            value = self.interval_class(value)
        return value


class IntRangeType(RangeType):
    """
    IntRangeType provides way for saving range of numbers into database.

    Example::


        from sqlalchemy_utils import IntRangeType


        class Event(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(255))
            estimated_number_of_persons = sa.Column(IntRangeType)


        party = Event(name=u'party')

        # we estimate the party to contain minium of 10 persons and at max
        # 100 persons
        party.estimated_number_of_persons = [10, 100]

        print party.estimated_number_of_persons
        # '10-100'


    IntRangeType returns the values as IntInterval objects. These objects
    support many arithmetic operators::


        meeting = Event(name=u'meeting')

        meeting.estimated_number_of_persons = [20, 40]

        total = (
            meeting.estimated_number_of_persons +
            party.estimated_number_of_persons
        )
        print total
        # '30-140'

    Good reading:

    http://wiki.postgresql.org/images/f/f0/Range-types.pdf
    """

    impl = INT4RANGE

    def __init__(self, *args, **kwargs):
        super(IntRangeType, self).__init__(*args, **kwargs)
        self.interval_class = intervals.IntInterval



class DateRangeType(RangeType):
    impl = DATERANGE

    def __init__(self, *args, **kwargs):
        super(DateRangeType, self).__init__(*args, **kwargs)
        self.interval_class = intervals.DateInterval

class NumericRangeType(RangeType):
    impl = NUMRANGE

    def __init__(self, *args, **kwargs):
        super(DateRangeType, self).__init__(*args, **kwargs)
        self.interval_class = intervals.DecimalInterval


class DateTimeRangeType(RangeType):
    impl = TSRANGE

    def __init__(self, *args, **kwargs):
        super(DateRangeType, self).__init__(*args, **kwargs)
        self.interval_class = intervals.DateTimeInterval
