import sqlalchemy as sa

from ..operators import CaseInsensitiveComparator


class EmailType(sa.types.TypeDecorator):
    impl = sa.Unicode
    comparator_factory = CaseInsensitiveComparator

    def __init__(self, length=255, *args, **kwargs):
        super(EmailType, self).__init__(length=length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.lower()
        return value

    @property
    def python_type(self):
        return self.impl.type.python_type
