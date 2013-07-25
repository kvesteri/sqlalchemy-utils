from functools import wraps
from sqlalchemy.orm.collections import InstrumentedList as _InstrumentedList
from sqlalchemy import types
from sqlalchemy.dialects.postgresql.base import ischema_names
from .arrow import ArrowType
from .color import ColorType
from .email import EmailType
from .ip_address import IPAddressType
from .number_range import (
    NumberRange,
    NumberRangeException,
    NumberRangeRawType,
    NumberRangeType,
)
from .password import Password, PasswordType
from .phone_number import PhoneNumber, PhoneNumberType
from .scalar_list import ScalarListException, ScalarListType
from .uuid import UUIDType


__all__ = (
    ArrowType,
    ColorType,
    EmailType,
    IPAddressType,
    NumberRange,
    NumberRangeException,
    NumberRangeRawType,
    NumberRangeType,
    Password,
    PasswordType,
    PhoneNumber,
    PhoneNumberType,
    ScalarListException,
    ScalarListType,
    UUIDType,
)


class TSVectorType(types.UserDefinedType):
    """
    Text search vector type for postgresql.
    """
    def get_col_spec(self):
        return 'tsvector'


ischema_names['tsvector'] = TSVectorType


class InstrumentedList(_InstrumentedList):
    """Enhanced version of SQLAlchemy InstrumentedList. Provides some
    additional functionality."""

    def any(self, attr):
        return any(getattr(item, attr) for item in self)

    def all(self, attr):
        return all(getattr(item, attr) for item in self)


def instrumented_list(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return InstrumentedList([item for item in f(*args, **kwargs)])
    return wrapper
