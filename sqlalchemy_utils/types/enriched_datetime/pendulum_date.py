from .pendulum_datetime import PendulumDatetime

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class PendulumDate(PendulumDatetime):
    def _coerce(self, impl, value):
        if value:
            if not isinstance(value, pendulum.Date):
                value = super(PendulumDate, self)._coerce(impl, value).date()
        return value

    def process_result_value(self, impl, value, dialect):
        if value:
            return pendulum.parse(value.isoformat()).date()
        return value

    def process_bind_param(self, impl, value, dialect):
        if value:
            return self._coerce(impl, value)
        return value
