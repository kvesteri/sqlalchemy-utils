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

jsonschema = None
try:
    import jsonschema
except ImportError:
    pass

try:
    from sqlalchemy.dialects.postgresql import JSON
    has_postgres_json = True
except ImportError:
    class PostgresJSONType(sa.types.UserDefinedType):
        """
        Text search vector type for postgresql.
        """
        def get_col_spec(self):
            return 'json'

    ischema_names['json'] = PostgresJSONType
    has_postgres_json = False


class JSONType(sa.types.TypeDecorator):
    """
    JSONType offers way of saving JSON data structures to database. On
    PostgreSQL the underlying implementation of this data type is 'json' while
    on other databases it's simply 'text'.

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


    If you have jsonschema_ installed, you may provide a schema :class:`dict` to the
    `schema` keyword and enjoy validation on commit.

    ::


        from sqlalchemy_utils import JSONType


        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(50))
            details = sa.Column(JSONType(schema={
                'type': 'object',
                'required': ['type'],
                'properties': {
                    'color': {'type': 'string'},
                    'max-speed': {'type': 'number'},
                    'type': {'type': 'string'},
                }
            }))


        product = Product()
        product.details = {
            'color': 'red',
            'type': 'car',
            'max-speed': '400 mph'
        }
        session.commit()
        # raises a sqlalchemy.exc.StatementError


    If not provided, the `validator` will be inferred from your schema,
    and a single instance stored for reuse through the life of your model
    class.

    If you need fine-grained control over how your validation works,
    specify an instance of an implementation of
    :class:`jsonschema.validators.IValidator`.

    .. _jsonschema: https://github.com/Julian/jsonschema
    """
    impl = sa.UnicodeText
    schema = None
    validator = None

    def __init__(self, schema=None, validator=None,
                 *args, **kwargs):
        if json is None:
            raise ImproperlyConfigured(
                'JSONType needs anyjson package installed.'
            )
        if schema is not None:
            if jsonschema is None:
                raise ImproperlyConfigured(
                    'JSONType needs the `jsonschema` package installed for'
                    ' JSON Schema validation'
                )
            self.schema = schema
            if validator is not None:
                self.validator = validator
            else:
                validator_cls = jsonschema.validators.validator_for(schema)
                validator_cls.check_schema(schema)
                self.validator = validator_cls(schema)
        super(JSONType, self).__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use the native JSON type.
            if has_postgres_json:
                return dialect.type_descriptor(JSON())
            else:
                return dialect.type_descriptor(PostgresJSONType())
        else:
            return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        if self.validator is not None:
            self.validator.validate(value, self.schema)
        if dialect.name == 'postgresql' and has_postgres_json:
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
