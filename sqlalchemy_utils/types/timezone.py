import functools
import pathlib
import zoneinfo

from sqlalchemy import types

from ..exceptions import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible


@functools.cache
def _available_timezones():
    return frozenset(zoneinfo.available_timezones())


def _dateutil_zone_key(tz):
    # dateutil sets ``_filename`` to the path of the file the zone was loaded
    # from, so recover the IANA key from the trailing path components. The
    # longest matching suffix wins so that e.g. ``Etc/UTC`` is not stored as
    # ``UTC``.
    parts = pathlib.PurePath(tz._filename).parts
    available = _available_timezones()
    for i in range(len(parts)):
        key = '/'.join(parts[i:])
        if key in available:
            return key
    raise ValueError('unable to determine time zone key for %r' % (tz,))


class TimezoneType(ScalarCoercible, types.TypeDecorator):
    """
    TimezoneType provides a way for saving timezones objects into database.
    TimezoneType saves timezone objects as strings on the way in and converts
    them back to objects when querying the database.

    ::

        from sqlalchemy_utils import TimezoneType

        class User(Base):
            __tablename__ = 'user'

            # Pass backend='pytz' to change it to use pytz. Other values:
            # 'dateutil' (default), and 'zoneinfo'.
            timezone = sa.Column(TimezoneType(backend='pytz'))

    :param backend:
        Whether to use 'dateutil', 'pytz' or 'zoneinfo' for timezones.
        'zoneinfo' uses the standard library module.

    """

    impl = types.Unicode(50)
    python_type = None
    cache_ok = True

    def __init__(self, backend='dateutil'):
        self.backend = backend
        if backend == 'dateutil':
            try:
                from dateutil.tz import gettz, tzfile

                def to_dateutil_zone(key):
                    if key not in _available_timezones():
                        return None
                    tz = gettz(key)
                    return tz if isinstance(tz, tzfile) else None

                self.python_type = tzfile
                self._to = to_dateutil_zone
                self._from = _dateutil_zone_key

            except ImportError:
                raise ImproperlyConfigured(
                    "'python-dateutil' is required to use the "
                    "'dateutil' backend for 'TimezoneType'"
                )

        elif backend == 'pytz':
            try:
                from pytz import timezone
                from pytz.tzinfo import BaseTzInfo

                self.python_type = BaseTzInfo
                self._to = timezone
                self._from = str

            except ImportError:
                raise ImproperlyConfigured(
                    "'pytz' is required to use the 'pytz' backend for 'TimezoneType'"
                )

        elif backend == 'zoneinfo':
            import zoneinfo

            self.python_type = zoneinfo.ZoneInfo
            self._to = zoneinfo.ZoneInfo
            self._from = str

        else:
            raise ImproperlyConfigured(
                "'pytz', 'dateutil' or 'zoneinfo' are the backends "
                "supported for 'TimezoneType'"
            )

    def _coerce(self, value):
        if value is not None and not isinstance(value, self.python_type):
            obj = self._to(value)
            if obj is None:
                raise ValueError("unknown time zone '%s'" % value)
            return obj
        return value

    def process_bind_param(self, value, dialect):
        return self._from(self._coerce(value)) if value else None

    def process_result_value(self, value, dialect):
        return self._to(value) if value else None
