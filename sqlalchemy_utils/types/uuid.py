from __future__ import absolute_import
import uuid
from sqlalchemy import types
from sqlalchemy.dialects import postgresql


class UUIDType(types.TypeDecorator):
    """
    Stores a UUID in the database natively when it can and falls back to
    a BINARY(16) or a CHAR(32) when it can't.
    """

    impl = types.BINARY(16)

    python_type = uuid.UUID

    def __init__(self, binary=True):
        """
        :param binary: Whether to use a BINARY(16) or CHAR(32) fallback.
        """
        self.binary = binary

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use the native UUID type.
            return dialect.type_descriptor(postgresql.UUID())

        else:
            # Fallback to either a BINARY or a CHAR.
            kind = self.impl if self.binary else types.CHAR(32)
            return dialect.type_descriptor(kind)

    @staticmethod
    def _coerce(value):
        if value and not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)

            except (TypeError, ValueError):
                value = uuid.UUID(bytes=value)

        return value

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, uuid.UUID):
            value = self._coerce(value)

        if dialect == 'postgresql':
            return str(value)

        return value.bytes if self.binary else value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if dialect == 'postgresql':
            return uuid.UUID(value)

        return uuid.UUID(bytes=value) if self.binary else uuid.UUID(value)

    def coercion_listener(self, target, value, oldvalue, initiator):
        return self._coerce(value)
