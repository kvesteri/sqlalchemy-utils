from __future__ import absolute_import

import six
from sqlalchemy import types

from ..exceptions import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class PendulumDateTimeType(types.TypeDecorator, ScalarCoercible):
    """
    Pendulum support.

    Example::


        from sqlalchemy_utils import PendulumDateType
        import pendulum


        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            birthday = sa.Column(PendulumDateType)


        user = User()
        user.birthday = pendulum.datetime(year=1995, month=7, day=11)
        session.add(user)
        session.commit()
    """
    impl = types.DateTime

    def __init__(self, *args, **kwargs):
        if not pendulum:
            raise ImproperlyConfigured(
                "'pendulum' package is required to use 'PendulumDateTimeType'"
            )

        super(PendulumDateTimeType, self).__init__(*args, **kwargs)

    @staticmethod
    def _coerce(value):
        if value:
            if isinstance(value, pendulum.DateTime):
                pass
            elif isinstance(value, int):
                value = pendulum.from_timestamp(value)
            elif isinstance(value, six.string_types) and value.isdigit():
                value = pendulum.from_timestamp(int(value))
            else:
                value = pendulum.parse(value)
        return value

    def process_bind_param(self, value, dialect):
        if value:
            return self._coerce(value).in_tz("UTC")
        return value

    def process_result_value(self, value, dialect):
        if value:
            return pendulum.parse(value.isoformat())
        return value

    def process_literal_param(self, value, dialect):
        return str(value)

    @property
    def python_type(self):
        return self.impl.type.python_type


class PendulumDateType(types.TypeDecorator, ScalarCoercible):
    """
    Pendulum support.

    Example::


        from sqlalchemy_utils import PendulumType
        import pendulum


        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            birthday = sa.Column(PendulumType)


        user = User()
        user.birthday = pendulum.datetime(year=1995, month=7, day=11)
        session.add(user)
        session.commit()
    """
    impl = types.Date

    def __init__(self, *args, **kwargs):
        if not pendulum:
            raise ImproperlyConfigured(
                "'pendulum' package is required to use 'PendulumDateType'"
            )

        super(PendulumDateType, self).__init__(*args, **kwargs)

    @staticmethod
    def _coerce(value):
        if value:
            if isinstance(value, pendulum.Date):
                pass
            elif isinstance(value, pendulum.DateTime):
                value = value.date()
            elif isinstance(value, int):
                value = pendulum.from_timestamp(value).date()
            elif isinstance(value, six.string_types) and value.isdigit():
                value = pendulum.from_timestamp(int(value)).date()
            else:
                value = pendulum.parse(value).date()
        return value

    def process_bind_param(self, value, dialect):
        if value:
            return self._coerce(value)
        return value

    def process_result_value(self, value, dialect):
        if value:
            return pendulum.parse(value.isoformat()).date()
        return value

    def process_literal_param(self, value, dialect):
        return str(value)

    @property
    def python_type(self):
        return self.impl.type.python_type
