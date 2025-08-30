import datetime

from ...exceptions import ImproperlyConfigured

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class PendulumDateTime:
    def __init__(self):
        if not pendulum:
            raise ImproperlyConfigured(
                "'pendulum' package is required to use 'PendulumDateTime'"
            )

    def _coerce(self, impl, value):
        if value is not None:
            if isinstance(value, pendulum.DateTime):
                pass
            elif isinstance(value, (int, float)):
                value = pendulum.from_timestamp(value)
            elif isinstance(value, str) and value.isdigit():
                value = pendulum.from_timestamp(int(value))
            elif isinstance(value, datetime.datetime):
                value = pendulum.DateTime.instance(value)
            else:
                value = pendulum.parse(value)
        return value

    def process_bind_param(self, impl, value, dialect):
        if value:
            return self._coerce(impl, value).in_tz('UTC').naive()
        return value

    def process_result_value(self, impl, value, dialect):
        if value:
            return pendulum.DateTime.instance(
                value.replace(tzinfo=datetime.timezone.utc)
            )
        return value
