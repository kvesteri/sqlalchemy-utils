furl = None
try:
    from furl import furl
except ImportError:
    pass
import six
from sqlalchemy import types
from .scalar_coercible import ScalarCoercible


class URLType(types.TypeDecorator, ScalarCoercible):
    impl = types.UnicodeText

    def process_bind_param(self, value, dialect):
        if isinstance(value, furl):
            return six.text_type(value)

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return furl(value)

    def _coerce(self, value):
        if value is not None and not isinstance(value, furl):
            return furl(value)
        return value
