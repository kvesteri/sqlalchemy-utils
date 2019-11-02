from datetime import datetime

import six

try:
    from collections.abc import Iterable
except ImportError:  # For python 2.7 support
    from collections import Iterable

arrow = None
try:
    import arrow
except ImportError:
    pass


class ArrowDatetime():
    def _coerce(self, value):
        if isinstance(value, six.string_types):
            value = arrow.get(value)
        elif isinstance(value, Iterable):
            value = arrow.get(*value)
        elif isinstance(value, datetime):
            value = arrow.get(value)
        return value

    def process_bind_param(self, value, dialect):
        if value:
            utc_val = self._coerce(value).to('UTC')
            return utc_val.datetime\
                if self.impl.timezone else utc_val.naive
        return value

    def process_result_value(self, value, dialect):
        if value:
            return arrow.get(value)
        return value
