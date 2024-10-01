import datetime

from sqlalchemy import types

from ..scalar_coercible import ScalarCoercible
from ...exceptions import ImproperlyConfigured

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class PendulumDateTime(types.TypeDecorator, ScalarCoercible):
    """Datetime column that uses PendulumDateTime as values.

    Example::


        from sqlalchemy_utils.enriched_datetime import PendulumDateTime
        import pendulum

        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            created_at = sa.Column(PendulumDateTime)

        user = User()
        user.created_at = pendulum.now()
        session.add(user)
        session.commit()
    """

    impl = types.DateTime
    cache_ok = True

    def __init__(self, *args, **kwargs):
        if not pendulum:
            raise ImproperlyConfigured(
                "'pendulum' package is required to use 'PendulumDateTime'"
            )
        super().__init__(*args, **kwargs)


    def _coerce(self, value):
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

    def process_bind_param(self, value, dialect):
        if value:
            return self._coerce(value).in_tz('UTC').naive()
        return value

    def process_result_value(self, value, dialect):
        if value:
            return pendulum.DateTime.instance(
                value.replace(tzinfo=datetime.timezone.utc)
            )
        return value

    def process_literal_param(self, value, dialect):
        return value


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
