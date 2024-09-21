from __future__ import annotations

from functools import total_ordering
from typing import Any

from .. import i18n
from ..utils import str_coercible


@str_coercible
@total_ordering
class WeekDay:
    NUM_WEEK_DAYS: int = 7

    def __init__(self, index: int) -> None:
        if not (0 <= index < self.NUM_WEEK_DAYS):
            raise ValueError(
                "index must be between 0 and %d" % self.NUM_WEEK_DAYS
            )
        self.index = index

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, WeekDay):
            return self.index == other.index
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self.index)

    def __lt__(self, other: WeekDay) -> bool:
        return self.position < other.position

    def __repr__(self):
        return f'{self.__class__.__name__}({self.index!r})'

    def __unicode__(self) -> str:
        return self.name

    def get_name(self, width: str = 'wide', context: str = 'format') -> str:
        names = i18n.babel.dates.get_day_names(
            width,
            context,
            i18n.get_locale()
        )
        return names[self.index]

    @property
    def name(self) -> str:
        return self.get_name()

    @property
    def position(self) -> int:
        return (
            self.index -
            i18n.get_locale().first_week_day
        ) % self.NUM_WEEK_DAYS
