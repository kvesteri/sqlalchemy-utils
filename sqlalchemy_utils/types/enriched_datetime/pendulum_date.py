from .pendulum_datetime import PendulumDatetime

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class PendulumDate(PendulumDatetime):
    def _coerce(self, value):
        if value:
            if not isinstance(value, pendulum.Date):
                value = super(PendulumDate, self)._coerce(value).date()
        return value

    def process_result_value(self, value, dialect):
        if value:
            return pendulum.parse(value.isoformat()).date()
        return value

    def process_bind_param(self, value, dialect):
        if value:
            return self._coerce(value)
        return value
