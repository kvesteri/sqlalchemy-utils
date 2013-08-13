import six
from sqlalchemy import types
from sqlalchemy_utils import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible


try:
    import colour
    from colour import Color

except ImportError:
    colour = None
    Color = None


class ColorType(types.TypeDecorator, ScalarCoercible):
    """
    Changes Color objects to a string representation on the way in and
    changes them back to Color objects on the way out.
    """
    STORE_FORMAT = u'hex'
    impl = types.Unicode(20)

    def __init__(self, max_length=20, *args, **kwargs):
        # Bail if colour is not found.
        if colour is None:
            raise ImproperlyConfigured(
                "'colour' package is required to use 'ColorType'"
            )

        super(ColorType, self).__init__(*args, **kwargs)
        self.impl = types.Unicode(max_length)

    def process_bind_param(self, value, dialect):
        if value:
            return six.text_type(getattr(value, self.STORE_FORMAT))
        return value

    def process_result_value(self, value, dialect):
        if value:
            return Color(value)
        return value

    def _coerce(self, value):
        if value is not None and not isinstance(value, Color):
            return Color(value)
        return value
