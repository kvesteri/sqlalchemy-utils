from __future__ import absolute_import
from collections import Iterable
from datetime import datetime
import six

arrow = None
try:
    import arrow
except:
    pass
from sqlalchemy import types
from sqlalchemy_utils import ImproperlyConfigured


class ArrowType(types.TypeDecorator):
    impl = types.DateTime

    def __init__(self, *args, **kwargs):
        if not arrow:
            raise ImproperlyConfigured(
                "'arrow' package is required to use 'ArrowType'"
            )

        super(ArrowType, self).__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value:
            return value.datetime
        return value

    def process_result_value(self, value, dialect):
        if value:
            return arrow.get(value)
        return value

    def coercion_listener(self, target, value, oldvalue, initiator):
        if value is None:
            return None
        elif isinstance(value, six.string_types):
            value = arrow.get(value)
        elif isinstance(value, Iterable):
            value = arrow.get(*value)
        elif isinstance(value, datetime):
            value = arrow.get(value)
        return value
