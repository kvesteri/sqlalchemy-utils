# -*- coding: utf-8 -*-
from sqlalchemy import types
from sqlalchemy.dialects.postgresql import BIT
import six
get_day_names = None
try:
    from babel.dates import get_day_names
except ImportError:
    pass

from ..compat import total_ordering
from ..exceptions import ImproperlyConfigured


@total_ordering
class WeekDay(object):
    NUM_WEEK_DAYS = 7
    get_locale = None

    def __init__(self, index, get_locale=None):
        if not (0 <= index < self.NUM_WEEK_DAYS):
            raise ValueError(
                "index must be between 0 and %d" % self.NUM_WEEK_DAYS
            )
        self.index = index

        if get_locale is not None:
            self.get_locale = get_locale

        if self.get_locale is None:
            raise ImproperlyConfigured(
                "Weekday class needs to define get_locale."
            )

    def __eq__(self, other):
        if isinstance(other, WeekDay):
            return self.index == other.index
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.index)

    def __lt__(self, other):
        return self.position < other.position

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.index)

    def __str__(self):
        return six.text_type(self).encode('utf-8')

    def __unicode__(self):
        return self.name

    def get_name(self, width='wide', context='format'):
        names = get_day_names(
            width,
            context,
            self.get_locale()
        )
        return names[self.index]

    @property
    def name(self):
        return self.get_name()

    @property
    def position(self):
        return (
            self.index -
            self.get_locale().first_week_day
        ) % self.NUM_WEEK_DAYS


class WeekDays(object):
    def __init__(self, bit_string_or_week_days):
        if isinstance(bit_string_or_week_days, six.string_types):
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

    def __eq__(self, other):
        if isinstance(other, WeekDays):
            return self._days == other._days
        elif isinstance(other, six.string_types):
            return self.as_bit_string() == other
        else:
            return NotImplemented

    def __iter__(self):
        for day in sorted(self._days):
            yield day

    def __contains__(self, value):
        return value in self._days

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.as_bit_string()
        )

    def __str__(self):
        return six.text_type(self).encode('utf-8')

    def __unicode__(self):
        return u', '.join(six.text_type(day) for day in self)

    def as_bit_string(self):
        return ''.join(
            '1' if WeekDay(index) in self._days else '0'
            for index in xrange(WeekDay.NUM_WEEK_DAYS)
        )


class WeekDaysType(types.TypeDecorator):
    impl = BIT(WeekDay.NUM_WEEK_DAYS)

    def process_bind_param(self, value, dialect):
        if isinstance(value, WeekDays):
            return value.as_bit_string()

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return WeekDays(value)
