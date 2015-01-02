import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy_utils import TSVectorType
from tests import TestCase


class TestTSVector(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            search_index = sa.Column(
                TSVectorType(name, regconfig='pg_catalog.finnish')
            )

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_generates_table(self):
        assert 'search_index' in self.User.__table__.c

    def test_type_reflection(self):
        reflected_metadata = sa.schema.MetaData()
        table = sa.schema.Table(
            'user',
            reflected_metadata,
            autoload=True,
            autoload_with=self.engine
        )
        assert isinstance(table.c['search_index'].type, TSVECTOR)

    def test_catalog_and_columns_as_args(self):
        type_ = TSVectorType('name', 'age', regconfig='pg_catalog.simple')
        assert type_.columns == ('name', 'age')
        assert type_.options['regconfig'] == 'pg_catalog.simple'

    def test_match(self):
        expr = self.User.search_index.match(u'something')
        assert str(expr.compile(self.connection)) == (
            '''"user".search_index @@ to_tsquery('pg_catalog.finnish', '''
            '''%(search_index_1)s)'''
        )

    def test_concat(self):
        assert str(self.User.search_index | self.User.search_index) == (
            '"user".search_index || "user".search_index'
        )

    def test_match_concatenation(self):
        concat = self.User.search_index | self.User.search_index
        bind = self.session.bind
        assert str(concat.match('something').compile(bind)) == (
            '("user".search_index || "user".search_index) @@ '
            "to_tsquery('pg_catalog.finnish', %(param_1)s)"
        )

    def test_match_with_catalog(self):
        expr = self.User.search_index.match(
            u'something',
            postgresql_regconfig='pg_catalog.simple'
        )
        assert str(expr.compile(self.connection)) == (
            '''"user".search_index @@ to_tsquery('pg_catalog.simple', '''
            '''%(search_index_1)s)'''
        )
