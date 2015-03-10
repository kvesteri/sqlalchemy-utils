"""JSONType definition."""

from __future__ import absolute_import

import six

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql.base import ischema_names

from ..exceptions import ImproperlyConfigured

json = None
try:
    import anyjson as json
except ImportError:
    import json as json

try:
    from sqlalchemy.dialects.postgresql import JSON
    has_postgres_json = True
except ImportError:
    class JSON(sa.types.UserDefinedType):
        """
        Text search vector type for postgresql.
        """
        def get_col_spec(self):
            return 'json'

    ischema_names['json'] = JSON
    has_postgres_json = False

try:
    from sqlalchemy.dialects.postgresql import JSONB
    has_postgres_jsonb = True
except ImportError:
    class JSONB(sa.types.UserDefinedType):
        """
        Text search vector type for postgresql.
        """
        def get_col_spec(self):
            return 'jsonb'

    ischema_names['jsonb'] = JSONB
    has_postgres_jsonb = False


class JSONType(sa.types.TypeDecorator):
    """
    JSONType offers way of saving JSON data structures to database. On
    PostgreSQL the underlying implementation of this data type is 'json' while
    on other databases its simply 'text'.

    ::


        from sqlalchemy_utils import JSONType


        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(50))
            details = sa.Column(JSONType)


        product = Product()
        product.details = {
            'color': 'red',
            'type': 'car',
            'max-speed': '400 mph'
        }
        session.commit()
    """

    impl = sa.UnicodeText

    def __init__(self, binary=True, impl=sa.UnicodeText, *args, **kwargs):
        if json is None:
            raise ImproperlyConfigured(
                'JSONType needs anyjson package installed.'
            )
        self.binary = binary
        self.engine_available = ((self.binary and has_postgres_jsonb) or
                                 (not self.binary and has_postgres_json))
        self.impl = impl
        super(JSONType, self).__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use the native JSONB or JSON type.
            if self.binary:
                return dialect.type_descriptor(JSONB())
            else:
                return dialect.type_descriptor(JSON())
        else:
            return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' and self.engine_available:
            return value
        if value is not None:
            value = six.text_type(json.dumps(value))
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            value = json.loads(value)
        return value
