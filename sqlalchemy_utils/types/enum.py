from __future__ import absolute_import

try:
    from enum import Enum
except ImportError:
    Enum = None

from sqlalchemy import types
from sqlalchemy_utils.exceptions import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible


class EnumType(types.TypeDecorator, ScalarCoercible):
    """
    EnumType offers way of integrating with :mod:`enum` in the standard
    library of Python 3.4+ or the enum34_ backported package on PyPI.

    .. _enum34: https://pypi.python.org/pypi/enum34

    ::

        from enum import Enum
        from sqlalchemy_utils import EnumType


        class OrderStatus(Enum):
            unpaid = 1
            paid = 2


        class Order(Base):
            __tablename__ = 'order'
            id = sa.Column(sa.Integer, autoincrement=True)
            status = sa.Column(EnumType(OrderStatus))


        order = Order()
        order.status = OrderStatus.unpaid
        session.add(order)
        session.commit()

        assert user.status is OrderStatus.unpaid
        assert user.status.value == 1
        assert user.status.name == 'paid'
    """

    impl = types.Integer

    def __init__(self, enum_class, impl=None, *args, **kwargs):
        if Enum is None:
            raise ImproperlyConfigured(
                "'enum34' package is required to use 'EnumType' in Python "
                "< 3.4")
        if not issubclass(enum_class, Enum):
            raise ImproperlyConfigured(
                "EnumType needs a class of enum defined.")

        super(EnumType, self).__init__(*args, **kwargs)
        self.enum_class = enum_class
        if impl is not None:
            self.impl = types.Integer

    def process_bind_param(self, value, dialect):
        return self.enum_class(value).value if value else None

    def process_result_value(self, value, dialect):
        return self.enum_class(value) if value else None

    def _coerce(self, value):
        return self.enum_class(value) if value else None
