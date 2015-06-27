import six

from decimal import Decimal

from sqlalchemy import types

from sqlalchemy_utils.exceptions import ImproperlyConfigured

from .scalar_coercible import ScalarCoercible

Price = None
try:
    from prices import Price
    python_price_type = Price
except ImportError:
    python_price_type = None


class PriceType(types.TypeDecorator, ScalarCoercible):
    """
    Changes :class:`.Price` objects to a decimal representation on the way in
    and changes them back to :class:`.Price` objects on the way out.

    In order to use PriceType you need to install prices_ first.

    .. _prices: https://github.com/mirumee/prices

    ::

        from prices import LinearTax, Price

        from sqlalchemy_utils import PriceType


        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(PriceType(precision=12, scale=2))


        product = Product()
        product.price = Price('6.5')
        session.add(product)
        session.commit()

        product.price  # Price('6.5')
        product.price.net  # Decimal('6.5')
        (product.price + LinearTax('0.20')).gross  # Decimal('7.8000')


    PriceType is scalar coercible::

        product.price = '3.99'
        product.price  # Price('3.99')
    """
    impl = types.Numeric
    python_type = python_price_type

    def __init__(self, *args, **kwargs):
        # Fail if prices is not found.
        if Price is None:
            raise ImproperlyConfigured(
                "'prices' package is required to use 'PriceType'"
            )

        super(PriceType, self).__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value:
            if isinstance(value, Price):
                return value.net
            elif isinstance(value, Decimal):
                return value
            elif isinstance(value, six.string_types):
                return Decimal(value)

        return value

    def process_result_value(self, value, dialect):
        if value:
            return Price(value)

        return value

    def _coerce(self, value):
        if value is not None and not isinstance(value, Price):
            return Price(value)

        return value
