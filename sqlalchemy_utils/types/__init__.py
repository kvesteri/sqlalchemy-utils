from functools import wraps
from sqlalchemy.orm.collections import InstrumentedList as _InstrumentedList
from .arrow import ArrowType
from .choice import ChoiceType, Choice
from .color import ColorType
from .country import CountryType, Country
from .email import EmailType
from .encrypted import EncryptedType
from .ip_address import IPAddressType
from .json import JSONType
from .locale import LocaleType
from .range import (
    DateRangeType,
    DateTimeRangeType,
    IntRangeType,
    NumericRangeType,
)
from .password import Password, PasswordType
from .phone_number import PhoneNumber, PhoneNumberType
from .scalar_list import ScalarListException, ScalarListType
from .timezone import TimezoneType
from .ts_vector import TSVectorType
from .url import URLType
from .uuid import UUIDType
from .weekdays import WeekDaysType


__all__ = (
    ArrowType,
    Choice,
    ChoiceType,
    ColorType,
    Country,
    CountryType,
    DateRangeType,
    DateTimeRangeType,
    EmailType,
    EncryptedType,
    IntRangeType,
    IPAddressType,
    JSONType,
    LocaleType,
    NumericRangeType,
    Password,
    PasswordType,
    PhoneNumber,
    PhoneNumberType,
    ScalarListException,
    ScalarListType,
    TimezoneType,
    TSVectorType,
    URLType,
    UUIDType,
    WeekDaysType,
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
