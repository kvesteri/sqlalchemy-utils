import six
import sqlalchemy as sa
from sqlalchemy import types


class ScalarListException(Exception):
    pass


class ScalarListType(types.TypeDecorator):
    impl = sa.UnicodeText()

    def __init__(self, coerce_func=six.text_type, separator=u','):
        self.separator = six.text_type(separator)
        self.coerce_func = coerce_func

    def process_bind_param(self, value, dialect):
        # Convert list of values to unicode separator-separated list
        # Example: [1, 2, 3, 4] -> u'1, 2, 3, 4'
        if value is not None:
            if any(self.separator in six.text_type(item) for item in value):
                raise ScalarListException(
                    "List values can't contain string '%s' (its being used as "
                    "separator. If you wish for scalar list values to contain "
                    "these strings, use a different separator string.)"
                )
            return self.separator.join(
                map(six.text_type, value)
            )

    def process_result_value(self, value, dialect):
        if value is not None:
            if value == u'':
                return []
            # coerce each value
            return list(map(
                self.coerce_func, value.split(self.separator)
            ))
