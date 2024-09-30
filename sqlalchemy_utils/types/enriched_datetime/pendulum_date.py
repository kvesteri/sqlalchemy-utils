from sqlalchemy import types

from ...exceptions import ImproperlyConfigured
from .pendulum_datetime import PendulumDateTime

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class PendulumDate(PendulumDateTime):

    cache_ok = True
    impl = types.Date

    def _coerce(self, value):
        if value:
            if not isinstance(value, pendulum.Date):
                value = super()._coerce(value).date()
        return value

    def process_result_value(self, value, dialect):
        if value:
            return pendulum.parse(value.isoformat()).date()
        return value

    def process_bind_param(self, value, dialect):
        if value:
            return self._coerce(value)
        return value
