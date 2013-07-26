import six
from sqlalchemy import types
from sqlalchemy_utils import ImproperlyConfigured


class TimezoneType(types.TypeDecorator):
    """
    Changes Timezone objects to a string representation on the way in and
    changes them back to Timezone objects on the way out.
    """

    impl = types.CHAR(50)

    python_type = None

    def __init__(self, backend='dateutil'):
        """
        :param backend: Whether to use 'dateutil' or 'pytz' for timezones.
        """

        self.backend = backend
        if backend == 'dateutil':
            try:
                from dateutil.tz import tzfile
                from dateutil.zoneinfo import gettz

                self.python_type = tzfile
                self._to = gettz
                self._from = lambda x: x._filename

            except ImportError:
                raise ImproperlyConfigured(
                    "'python-dateutil' is required to use the "
                    "'dateutil' backend for 'TimezoneType'"
                )

        elif backend == 'pytz':
            try:
                from pytz import tzfile, timezone

                self.python_type = tzfile.DstTzInfo
                self._to = timezone
                self._from = six.text_type

            except ImportError:
                raise ImproperlyConfigured(
                    "'pytz' is required to use the 'pytz' backend "
                    "for 'TimezoneType'"
                )

        else:
            raise ImproperlyConfigured(
                "'pytz' or 'dateutil' are the backends supported for "
                "'TimezoneType'"
            )

    def _coerce(self, value):
        if value and not isinstance(value, self.python_type):
            obj = self._to(value)
            if obj is None:
                raise ValueError("unknown time zone '%s'" % value)

            return obj

        return value

    def coercion_listener(self, target, value, oldvalue, initiator):
        return self._coerce(value)

    def process_bind_param(self, value, dialect):
        return self._from(self._coerce(value)) if value else None

    def process_result_value(self, value, dialect):
        return self._to(value) if value else None
