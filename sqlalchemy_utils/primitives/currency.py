from __future__ import annotations

from typing import Any, Union

from .. import i18n, ImproperlyConfigured
from ..utils import str_coercible


@str_coercible
class Currency:
    """
    Currency class wraps a 3-letter currency code. It provides various
    convenience properties and methods.

    ::

        from babel import Locale
        from sqlalchemy_utils import Currency, i18n


        # First lets add a locale getter for testing purposes
        i18n.get_locale = lambda: Locale('en')


        Currency('USD').name  # US Dollar
        Currency('USD').symbol  # $

        Currency(Currency('USD')).code  # 'USD'

    Currency always validates the given code if you use at least the optional
    dependency list 'babel', otherwise no validation are performed.

    ::

        Currency(None)  # raises TypeError

        Currency('UnknownCode')  # raises ValueError


    Currency supports equality operators.

    ::

        Currency('USD') == Currency('USD')
        Currency('USD') != Currency('EUR')


    Currencies are hashable.


    ::

        len(set([Currency('USD'), Currency('USD')]))  # 1


    """
    def __init__(self, code: Union[Currency, str]) -> None:
        if i18n.babel is None:
            raise ImproperlyConfigured(
                "'babel' package is required in order to use Currency class."
            )
        if isinstance(code, Currency):
            self.code = code
        elif isinstance(code, str):
            self.validate(code)
            self.code = code
        else:
            raise TypeError(
                'First argument given to Currency constructor should be '
                'either an instance of Currency or valid three letter '
                'currency code.'
            )

    @classmethod
    def validate(self, code: str) -> None:
        try:
            i18n.babel.Locale('en').currencies[code]
        except KeyError:
            raise ValueError(f"'{code}' is not valid currency code.")
        except AttributeError:
            # As babel is optional, we may raise an AttributeError accessing it
            pass

    @property
    def symbol(self) -> str:
        return i18n.babel.numbers.get_currency_symbol(
            self.code,
            i18n.get_locale()
        )

    @property
    def name(self) -> str:
        return i18n.get_locale().currencies[self.code]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Currency):
            return self.code == other.code
        elif isinstance(other, str):
            return self.code == other
        else:
            return NotImplemented

    def __ne__(self, other: Any) -> bool:
        return not (self == other)

    def __hash__(self) -> int:
        return hash(self.code)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.code!r})'

    def __unicode__(self) -> str:
        return self.code
