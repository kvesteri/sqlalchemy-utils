from __future__ import absolute_import
import calendar
import datetime
import decimal
import uuid
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from .scalar_coercible import ScalarCoercible


class DateTimeType(types.TypeDecorator):
    """
    Stores a timestamp in the database natively or as a float as some backend
    do not support precise timestamps up to the microsecond.

    ::

        from sqlalchemy_utils import DateTimeType

        class User(Base):
            __tablename__ = 'user'

            timestamp = sa.Column(DateTimeType)
    """

    impl = types.DateTime

    python_type = datetime.datetime

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(types.DECIMAL(precision=20,
                                                         scale=6,
                                                         asdecimal=True))
        return self.impl

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'mysql':
            decimal.getcontext().prec = 30
            return (decimal.Decimal(str(calendar.timegm(value.utctimetuple())))
                    + (decimal.Decimal(str(value.microsecond)) /
                       decimal.Decimal("1000000.0")))
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'mysql':
            integer = int(value)
            micro = ((value - decimal.Decimal(integer))
                     * decimal.Decimal(1000 ** 2))
            daittyme = datetime.datetime.utcfromtimestamp(integer)
            return daittyme.replace(microsecond=int(round(micro)))
        return value
