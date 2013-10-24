from sqlalchemy import types
import six
from .scalar_coercible import ScalarCoercible
from ..exceptions import ImproperlyConfigured
babel = None
try:
    import babel
except ImportError:
    pass


class LocaleType(types.TypeDecorator, ScalarCoercible):
    """
    Changes babel.Locale objects to a string representation on the way in and
    changes them back to Locale objects on the way out.
    """

    impl = types.Unicode(10)

    def __init__(self):
        if babel is None:
            raise ImproperlyConfigured(
                'Babel packaged is required with LocaleType.'
            )

    def process_bind_param(self, value, dialect):
        if isinstance(value, babel.Locale):
            return six.text_type(value)

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return babel.Locale(value)

    def _coerce(self, value):
        if value is not None and not isinstance(value, babel.Locale):
            return babel.Locale(value)
        return value
