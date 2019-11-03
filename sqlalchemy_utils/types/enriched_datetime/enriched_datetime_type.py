from sqlalchemy import types

from ...exceptions import ImproperlyConfigured
from ..scalar_coercible import ScalarCoercible
from .arrow_datetime import ArrowDatetime
from .pendulum_datetime import PendulumDatetime

arrow = None
try:
    import arrow
except ImportError:
    pass

pendulum = None
try:
    import pendulum
except ImportError:
    pass


class EnrichedDateTimeType(types.TypeDecorator, ScalarCoercible):
    """
    Supported for arrow and pendulum.

    Example::


        from sqlalchemy_utils import EnrichedDateTimeType
        import pendulum


        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            created_at = sa.Column(EnrichedDateTimeType(type="pendulum"))
            # created_at = sa.Column(EnrichedDateTimeType(type="arrow"))


        user = User()
        user.created_at = pendulum.now()
        session.add(user)
        session.commit()
    """
    impl = types.DateTime

    def __init__(self, type="pendulum", *args, **kwargs):
        self.type = type
        if type == "pendulum":
            if not pendulum:
                raise ImproperlyConfigured(
                    "'pendulum' package is required"
                    " to use 'EnrichedDateTimeType'"
                )
            else:
                super(EnrichedDateTimeType, self).__init__(*args, **kwargs)
                self.dt_object = PendulumDatetime()
        elif type == "arrow":
            if not arrow:
                raise ImproperlyConfigured(
                    "'arrow' package is required to use 'EnrichedDateTimeType'"
                )
            else:
                super(EnrichedDateTimeType, self).__init__(*args, **kwargs)
                self.dt_object = ArrowDatetime()

    def _coerce(self, value):
        return self.dt_object._coerce(self.impl, value)

    def process_bind_param(self, value, dialect):
        return self.dt_object.process_bind_param(self.impl, value, dialect)

    def process_result_value(self, value, dialect):
        return self.dt_object.process_result_value(self.impl, value, dialect)

    def process_literal_param(self, value, dialect):
        return str(value)

    @property
    def python_type(self):
        return self.impl.type.python_type
