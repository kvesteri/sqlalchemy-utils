from datetime import datetime

import six

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class PendulumDatetime():
    def _coerce(self, impl, value):
        if value is not None:
            if isinstance(value, pendulum.DateTime):
                pass
            elif isinstance(value, int):
                value = pendulum.from_timestamp(value)
            elif isinstance(value, six.string_types) and value.isdigit():
                value = pendulum.from_timestamp(int(value))
            elif isinstance(value, datetime):
                value = pendulum.datetime(value.year,
                                          value.month, value.day,
                                          value.hour, value.minute,
                                          value.second, value.microsecond)
            else:
                value = pendulum.parse(value)

    def process_bind_param(self, impl, value, dialect):
        if value:
            return self._coerce(value).in_tz("UTC")
        return value

    def process_result_value(self, impl, value, dialect):
        if value:
            return pendulum.parse(value.isoformat())
        return value
