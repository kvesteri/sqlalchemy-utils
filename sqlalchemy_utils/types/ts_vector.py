import sqlalchemy as sa
from sqlalchemy.dialects.postgresql.base import ischema_names


class TSVectorType(sa.types.UserDefinedType):
    """
    Text search vector type for postgresql.
    """
    def get_col_spec(self):
        return 'tsvector'


ischema_names['tsvector'] = TSVectorType
