from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import types

from ..scalar_coercible import ScalarCoercible
from ...exceptions import ImproperlyConfigured

arrow = None
try:
    import arrow
except ImportError:
    pass


class ArrowDateTime(types.TypeDecorator, ScalarCoercible):
    """Datetime column that uses arrow dates.

    Example::


        from sqlalchemy_utils.enriched_datetime import ArrowDateTime
        import arrow

        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            created_at = sa.Column(ArrowDateTime)

        user = User()
        user.created_at = arrow.now()
        session.add(user)
        session.commit()
    """
    impl = types.DateTime
    cache_ok = True

    def __init__(self, *args, **kwargs):
        if not arrow:
            raise ImproperlyConfigured(
                "'arrow' package is required to use 'ArrowDateTime'"
            )
        super().__init__(*args, **kwargs)

    def _coerce(self, value):
        if isinstance(value, str):
            value = arrow.get(value)
        elif isinstance(value, Iterable):
            value = arrow.get(*value)
        elif isinstance(value, datetime):
            value = arrow.get(value)
        return value

    def process_bind_param(self, value, dialect):
        if value:
            utc_val = self._coerce(value).to('UTC')
            return utc_val.datetime\
                if self.impl.timezone else utc_val.naive
        return value

    def process_result_value(self, value, dialect):
        if value:
            return arrow.get(value)
        return value

    def process_literal_param(self, value, dialect):
        return value
