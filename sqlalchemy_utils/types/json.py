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
    class PostgresJSONType(sa.types.UserDefinedType):
        """
        Text search vector type for postgresql.
        """
        def get_col_spec(self):
            return 'json'

    ischema_names['json'] = PostgresJSONType
    has_postgres_json = False


class JSONType(sa.types.TypeDecorator):
    '''
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

    Python's JSON module doesn't have native support for encoding and decoding
    all data types -- most notably, it chokes on datetime objects. By passing
    custom subclasses of :class:`~json.JSONEncoder` and
    :class:`~json.JSONDecoder` to JSONType, you can teach it how to encode
    and decode any data type you wish. For example, to handle datetime objects,
    you can do the following::

        import json
        import datetime
        import re
        from sqlalchemy_utils import JSONType


        DATETIME_ISO_RE = re.compile(r"""
            (?P<year>\d{4})-
            (?P<month>\d{2})-
            (?P<day>\d{2})T
            (?P<hour>\d{2}):
            (?P<minute>\d{2}):
            (?P<second>\d{2})
        """, re.VERBOSE)

        class CustomJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime.datetime):
                    return obj.replace(microsecond=0).isoformat()
                return super(CustomJSONEncoder, self).default(obj)

        class CustomJSONDecoder(json.JSONDecoder):
            def decode(self, obj):
                match = DATETIME_ISO_RE.match(obj)
                if match:
                    return datetime.datetime(
                        year=int(match.group('year')),
                        month=int(match.group('month')),
                        day=int(match.group('day')),
                        hour=int(match.group('hour')),
                        minute=int(match.group('minute')),
                        second=int(match.group('second')),
                    )
                return super(CustonJSONDecoder, self).decode(obj)

        class Product(Base):
            __tablename__ = 'person'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(50))
            details = sa.Column(JSONType,
                encode_cls=CustomJSONEncoder,
                decode_cls=CustomJSONDecoder,
            )


        product = Product()
        product.details = {
            'constructed': datetime(2016, 2, 15, 14, 15, 0)
        }
        session.commit()

    For more information, read the documentation for :class:`json.JSONEncoder`
    and :class:`json.JSONDecoder`.

    '''
    impl = sa.UnicodeText

    def __init__(self, encode_cls=None, decode_cls=None, *args, **kwargs):
        if json is None:
            raise ImproperlyConfigured(
                'JSONType needs anyjson package installed.'
            )
        self.encode_cls = encode_cls
        self.decode_cls = decode_cls
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
        if dialect.name == 'postgresql' and has_postgres_json:
            return value
        if value is not None:
            value = six.text_type(json.dumps(value, cls=self.encode_cls))
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            value = json.loads(value, cls=self.decode_cls)
        return value
