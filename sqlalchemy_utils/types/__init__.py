from functools import wraps
from sqlalchemy.orm.collections import InstrumentedList as _InstrumentedList
from .arrow import ArrowType
from .color import ColorType
from .country import CountryType, Country
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
from .timezone import TimezoneType
from .ts_vector import TSVectorType
from .uuid import UUIDType
from .weekdays import WeekDay, WeekDays, WeekDaysType


__all__ = (
    ArrowType,
    ColorType,
    CountryType,
    Country,
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
    TimezoneType,
    TSVectorType,
    UUIDType,
    WeekDay,
    WeekDays,
    WeekDaysType
)


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
