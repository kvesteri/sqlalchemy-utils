# -*- coding: utf-8 -*-
from collections import Iterable
from decimal import Decimal
try:
    from functools import total_ordering
except ImportError:
    from total_ordering import total_ordering

import six


class NumberRangeException(Exception):
    pass


class RangeBoundsException(NumberRangeException):
    def __init__(self, min_value, max_value):
        self.message = 'Min value %s is bigger than max value %s.' % (
            min_value,
            max_value
        )


def is_number(number):
    return isinstance(number, (float, int, Decimal))


def parse_number(number):
    if number is None or number == '':
        return None
    elif is_number(number):
        return number
    else:
        return int(number)


@total_ordering
class NumberRange(object):
    def __init__(self, *args):
        """
        Parses given args and assigns lower and upper bound for this number
        range.

        1. Comma separated string argument

        ::


            >>> range = NumberRange('[23, 45]')
            >>> range.lower
            23
            >>> range.upper
            45


            >>> range = NumberRange('(23, 45]')
            >>> range.lower_inc
            False

            >>> range = NumberRange('(23, 45)')
            >>> range.lower_inc
            False
            >>> range.upper_inc
            False

        2. Sequence of arguments

        ::


            >>> range = NumberRange(23, 45)
            >>> range.lower
            23
            >>> range.upper
            45


        3. Lists and tuples as an argument

        ::


            >>> range = NumberRange([23, 45])
            >>> range.lower
            23
            >>> range.upper
            45
            >>> range.closed
            True


            >>> range = NumberRange((23, 45))
            >>> range.lower
            23
            >>> range.closed
            False

        4. Integer argument

        ::


            >>> range = NumberRange(34)
            >>> range.lower == range.upper == 34
            True


        5. Object argument

        ::

            >>> range = NumberRange(NumberRange(20, 30))
            >>> range.lower
            20
            >>> range.upper
            30

        """
        if len(args) > 2:
            raise NumberRangeException(
                'NumberRange takes at most two arguments'
            )
        elif len(args) == 2:
            self.parse_sequence(args)
        else:
            arg, = args
            if isinstance(arg, six.integer_types):
                self.parse_integer(arg)
            elif isinstance(arg, six.string_types):
                self.parse_string(arg)
            elif isinstance(arg, Iterable):
                self.parse_sequence(arg)
            elif hasattr(arg, 'lower') and hasattr(arg, 'upper'):
                self.parse_object(arg)

        if self.lower > self.upper:
            raise RangeBoundsException(self.lower, self.upper)

    @property
    def lower(self):
        return self._lower

    @lower.setter
    def lower(self, value):
        if value is None:
            self._lower = -float('inf')
        else:
            self._lower = value

    @property
    def upper(self):
        return self._upper

    @upper.setter
    def upper(self, value):
        if value is None:
            self._upper = float('inf')
        else:
            self._upper = value

    @property
    def open(self):
        """
        Returns whether or not this object is an open interval.

        ::

            range = NumberRange('(23, 45)')
            range.open  # True

            range = NumberRange('[23, 45]')
            range.open  # False
        """
        return not self.lower_inc and not self.upper_inc

    @property
    def closed(self):
        """
        Returns whether or not this object is a closed interval.

        ::

            range = NumberRange('(23, 45)')
            range.closed  # False

            range = NumberRange('[23, 45]')
            range.closed  # True
        """
        return self.lower_inc and self.upper_inc

    def parse_object(self, obj):
        self.lower = obj.lower
        self.upper = obj.upper
        self.lower_inc = obj.lower_inc
        self.upper_inc = obj.upper_inc

    def parse_string(self, value):
        if ',' not in value:
            self.parse_hyphen_range(value)
        else:
            self.parse_bounded_range(value)

    def parse_sequence(self, seq):
        lower, upper = seq
        self.lower = parse_number(lower)
        self.upper = parse_number(upper)
        if isinstance(seq, tuple):
            self.lower_inc = self.upper_inc = False
        else:
            self.lower_inc = self.upper_inc = True

    def parse_integer(self, value):
        self.lower = self.upper = value
        self.lower_inc = self.upper_inc = True

    def parse_bounded_range(self, value):
        values = value.strip()[1:-1].split(',')
        try:
            lower, upper = map(
                lambda a: parse_number(a.strip()), values
            )
        except ValueError as e:
            raise NumberRangeException(e.message)

        self.lower_inc = value[0] == '['
        self.upper_inc = value[-1] == ']'
        self.lower = lower
        self.upper = upper

    def parse_hyphen_range(self, value):
        values = value.split('-')
        if len(values) == 1:
            self.lower = self.upper = parse_number(value.strip())
        else:
            try:
                self.lower, self.upper = map(
                    lambda a: parse_number(a.strip()), values
                )
            except ValueError as e:
                raise NumberRangeException(str(e))
        self.lower_inc = self.upper_inc = True

    @property
    def normalized(self):
        return '%s%s, %s%s' % (
            '[' if self.lower_inc else '(',
            self.lower if self.lower != -float('inf') else '',
            self.upper if self.upper != float('inf') else '',
            ']' if self.upper_inc else ')'
        )

    def __eq__(self, other):
        if isinstance(other, six.integer_types):
            return self.lower == other == self.upper
        try:
            return (
                self.lower == other.lower and
                self.upper == other.upper
            )
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __gt__(self, other):
        if isinstance(other, six.integer_types):
            return self.lower > other and self.upper > other

        try:
            return self.lower > other.lower and self.upper > other.upper
        except AttributeError:
            return NotImplemented

    def __repr__(self):
        return 'NumberRange(%r, %r)' % (self.lower, self.upper)

    def __str__(self):
        if self.lower != self.upper:
            return '%s - %s' % (self.lower, self.upper)
        return str(self.lower)

    def __add__(self, other):
        """
        [a, b] + [c, d] = [a + c, b + d]
        """
        try:
            return NumberRange(
                self.lower + other.lower,
                self.upper + other.upper
            )
        except AttributeError:
            return NotImplemented

    def __sub__(self, other):
        """
        Defines the substraction operator.

        As defined in wikipedia:

        [a, b] − [c, d] = [a − d, b − c]
        """
        try:
            return NumberRange(
                self.lower - other.upper,
                self.upper - other.lower
            )
        except AttributeError:
            return NotImplemented
