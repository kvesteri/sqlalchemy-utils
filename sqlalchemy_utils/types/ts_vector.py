import sqlalchemy as sa
from sqlalchemy.dialects.postgresql.base import ischema_names


class TSVectorType(sa.types.UserDefinedType):
    class comparator_factory(sa.types.TypeEngine.Comparator):
        def match(self, other):
            from sqlalchemy_utils.expressions import tsvector_match

            return tsvector_match(self.expr, other)

    def __init__(self, *args, **kwargs):
        """
        Initializes new TSVectorType

        :param *args: list of column names
        :param **kwargs: various other options for this TSVectorType
        """
        self.columns = args
        self.options = kwargs

    """
    Text search vector type for postgresql.
    """
    def get_col_spec(self):
        return 'tsvector'


ischema_names['tsvector'] = TSVectorType
