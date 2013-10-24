import sqlalchemy as sa

json = None
try:
    import anyjson as json
except ImportError:
    pass

import six
from sqlalchemy.dialects.postgresql.base import ischema_names
from ..exceptions import ImproperlyConfigured


class PostgresJSONType(sa.types.UserDefinedType):
    """
    Text search vector type for postgresql.
    """
    def get_col_spec(self):
        return 'json'


ischema_names['json'] = PostgresJSONType


class JSONType(sa.types.TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = sa.UnicodeText

    def __init__(self):
        if json is None:
            raise ImproperlyConfigured(
                'JSONType needs anyjson package installed.'
            )

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use the native JSON type.
            return dialect.type_descriptor(PostgresJSONType())
        else:
            return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = six.text_type(json.dumps(value))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value
