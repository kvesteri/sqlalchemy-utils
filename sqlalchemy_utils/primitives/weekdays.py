from __future__ import annotations

from typing import Any, Generator, Hashable, Union

from .weekday import WeekDay
from ..utils import str_coercible


@str_coercible
class WeekDays:
    _days: set

    def __init__(self, bit_string_or_week_days: Union[str, WeekDays, Hashable]) -> None:
        if isinstance(bit_string_or_week_days, str):
            self._days = set()

            if len(bit_string_or_week_days) != WeekDay.NUM_WEEK_DAYS:
                raise ValueError(
                    'Bit string must be {0} characters long.'.format(
                        WeekDay.NUM_WEEK_DAYS
                    )
                )

            for index, bit in enumerate(bit_string_or_week_days):
                if bit not in '01':
                    raise ValueError(
                        'Bit string may only contain zeroes and ones.'
                    )
                if bit == '1':
                    self._days.add(WeekDay(index))
        elif isinstance(bit_string_or_week_days, WeekDays):
            self._days = bit_string_or_week_days._days
        else:
            self._days = set(bit_string_or_week_days)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, WeekDays):
            return self._days == other._days
        elif isinstance(other, str):
            return self.as_bit_string() == other
        else:
            return NotImplemented

    def __iter__(self) -> Generator[WeekDay, None, None]:
        for day in sorted(self._days):
            yield day

    def __contains__(self, value: Any) -> bool:
        return value in self._days

    def __repr__(self) -> str:
        return '%s(%r)' % (
            self.__class__.__name__,
            self.as_bit_string()
        )

    def __unicode__(self) -> str:
        return ', '.join(str(day) for day in self)

    def as_bit_string(self) -> str:
        return ''.join(
            '1' if WeekDay(index) in self._days else '0'
            for index in range(WeekDay.NUM_WEEK_DAYS)
        )
