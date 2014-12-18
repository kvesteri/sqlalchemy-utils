from sqlalchemy import types
from .scalar_coercible import ScalarCoercible
from ..exceptions import ImproperlyConfigured
Money = None
try:
    from money import Money
except ImportError:
    pass


if Money is not None:

    class MoneyComposite(Money):

        def __composite_values__(self):
            return (self.amount, self.currency)


else:

    class MoneyComposite(object):

        def __init__(self, amount, currency):
            self.amount = amount
            self.currency = currency
