import six
from sqlalchemy import types
from sqlalchemy.dialects.postgresql import BIT
from sqlalchemy_utils.primitives import WeekDay, WeekDays


class WeekDaysType(types.TypeDecorator):
    impl = BIT(WeekDay.NUM_WEEK_DAYS)

    def process_bind_param(self, value, dialect):
        if isinstance(value, WeekDays):
            return value.as_bit_string()

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return WeekDays(value)
