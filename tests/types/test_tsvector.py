import six
import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType
from tests import TestCase


class TestTSVector(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            search_index = sa.Column(TSVectorType())

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_generates_table(self):
        assert 'search_index' in self.User.__table__.c

    def test_type_autoloading(self):
        reflected_metadata = sa.schema.MetaData()
        table = sa.schema.Table(
            'user',
            reflected_metadata,
            autoload=True,
            autoload_with=self.engine
        )
        assert isinstance(table.c['search_index'].type, TSVectorType)

    def test_catalog_and_columns_as_args(self):
        type_ = TSVectorType('name', 'age', catalog='pg_catalog.simple')
        assert type_.columns == ('name', 'age')
        assert type_.options['catalog'] == 'pg_catalog.simple'

    def test_match(self):
        expr = self.User.search_index.match_tsquery(u'something')
        assert six.text_type(expr) == (
            '("user".search_index) @@ to_tsquery(:to_tsquery_1)'
        )

    def test_match_with_catalog(self):
        expr = self.User.search_index.match_tsquery(
            u'something', catalog='pg_catalog.simple'
        )
        assert six.text_type(expr) == (
            '("user".search_index) @@ to_tsquery(:to_tsquery_1, :to_tsquery_2)'
        )
