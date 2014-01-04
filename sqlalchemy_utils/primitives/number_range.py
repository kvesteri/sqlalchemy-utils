# -*- coding: utf-8 -*-
try:
    from functools import total_ordering
except ImportError:
    from total_ordering import total_ordering

import six


class NumberRangeException(Exception):
    pass


class RangeBoundsException(NumberRangeException):
    def __init__(self, min_value, max_value):
        self.message = 'Min value %d is bigger than max value %d.' % (
            min_value,
            max_value
        )


def parse_number(number):
    if (
        number == float('inf') or
        number == -float('inf') or
        number is None or
        number == ''
    ):
        return None
    else:
        return int(number)


@total_ordering
class NumberRange(object):
    def __init__(self, *args):
        if len(args) > 2:
            raise NumberRangeException(
                'NumberRange takes at most two arguments'
            )
        elif len(args) == 2:
            lower, upper = args
            if lower > upper:
                raise RangeBoundsException(lower, upper)
            self.lower = parse_number(lower)
            self.upper = parse_number(upper)
            self.lower_inc = self.upper_inc = True
        else:
            arg, = args
            if isinstance(arg, six.integer_types):
                self.lower = self.upper = arg
                self.lower_inc = self.upper_inc = True
            elif isinstance(arg, six.string_types):
                if ',' not in arg:
                    self.lower, self.upper = self.parse_range(arg)
                    self.lower_inc = self.upper_inc = True
                else:
                    self.from_range_with_bounds(arg)
            elif hasattr(arg, 'lower') and hasattr(arg, 'upper'):
                self.lower = arg.lower
                self.upper = arg.upper
                if not arg.lower_inc:
                    self.lower += 1

                if not arg.upper_inc:
                    self.upper -= 1

    def from_range_with_bounds(self, value):
        """
        Returns new NumberRange object from normalized number range format.

        Example ::

            range = NumberRange('[23, 45]')
            range.lower = 23
            range.upper = 45

            range = NumberRange('(23, 45]')
            range.lower = 24
            range.upper = 45

            range = NumberRange('(23, 45)')
            range.lower = 24
            range.upper = 44
        """
        values = value.strip()[1:-1].split(',')
        try:
            lower, upper = map(
                lambda a: parse_number(a.strip()), values
            )
        except ValueError as e:
            raise NumberRangeException(e.message)

        self.lower_inc = value[0] == '('
        if self.lower_inc:
            lower += 1

        self.upper_inc = value[-1] == ')'
        if self.upper_inc:
            upper -= 1

        self.lower = lower
        self.upper = upper

    def parse_range(self, value):
        if value is not None:
            values = value.split('-')
            if len(values) == 1:
                lower = upper = parse_number(value.strip())
            else:
                try:
                    lower, upper = map(
                        lambda a: parse_number(a.strip()), values
                    )
                except ValueError as e:
                    raise NumberRangeException(str(e))
            return lower, upper

    @property
    def normalized(self):
        return '[%s, %s]' % (
            self.lower if self.lower is not None else '',
            self.upper if self.upper is not None else ''
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
