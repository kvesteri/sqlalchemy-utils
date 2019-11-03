from sqlalchemy import types

from ...exceptions import ImproperlyConfigured
from ..scalar_coercible import ScalarCoercible

from .pendulum_date import PendulumDate

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class EnrichedDateType(types.TypeDecorator, ScalarCoercible):
    """
    Supported for pendulum only.

    Example::


        from sqlalchemy_utils import EnrichedDateType
        import pendulum


        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            birthday = sa.Column(EnrichedDateType(type="pendulum"))


        user = User()
        user.birthday = pendulum.datetime(year=1995, month=7, day=11)
        session.add(user)
        session.commit()
    """
    impl = types.Date

    def __init__(self, type="pendulum", *args, **kwargs):
        self.type = type
        if type == "pendulum":
            if not pendulum:
                raise ImproperlyConfigured(
                    "'pendulum' package is required"
                    " to use 'EnrichedDateTimeType'"
                )
            else:
                super(EnrichedDateType, self).__init__(*args, **kwargs)
                self.date_object = PendulumDate(*args, **kwargs)

    def _coerce(self, value):
        return self.date_object._coerce(value)

    def process_bind_param(self, value, dialect):
        return self.date_object.process_bind_param(value, dialect)

    def process_result_value(self, value, dialect):
        return self.date_object.process_result_value(value, dialect)

    def process_literal_param(self, value, dialect):
        return str(value)

    @property
    def python_type(self):
        return self.impl.type.python_type