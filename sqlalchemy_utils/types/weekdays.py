import six
from sqlalchemy import types
from sqlalchemy_utils.primitives import WeekDay, WeekDays
from .scalar_coercible import ScalarCoercible
from .bit import BitType


class WeekDaysType(types.TypeDecorator, ScalarCoercible):
    impl = BitType(WeekDay.NUM_WEEK_DAYS)

    def process_bind_param(self, value, dialect):
        if isinstance(value, WeekDays):
            return value.as_bit_string()

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return WeekDays(value)

    def _coerce(self, value):
        if value is not None and not isinstance(value, WeekDays):
            return WeekDays(value)
        return value
