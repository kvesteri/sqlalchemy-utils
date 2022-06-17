import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

from sqlalchemy_utils import TSVectorType


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        search_index = sa.Column(
            TSVectorType(name, regconfig='pg_catalog.finnish')
        )

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestTSVector:
    def test_generates_table(self, User):
        assert 'search_index' in User.__table__.c

    @pytest.mark.usefixtures('session')
    def test_type_reflection(self, engine):
        reflected_metadata = sa.schema.MetaData()
        table = sa.schema.Table(
            'user',
            reflected_metadata,
            autoload_with=engine,
        )
        assert isinstance(table.c['search_index'].type, TSVECTOR)

    def test_catalog_and_columns_as_args(self):
        type_ = TSVectorType('name', 'age', regconfig='pg_catalog.simple')
        assert type_.columns == ('name', 'age')
        assert type_.options['regconfig'] == 'pg_catalog.simple'

    def test_match(self, connection, User):
        expr = User.search_index.match('something')
        assert str(expr.compile(connection)) == (
            '''"user".search_index @@ to_tsquery('pg_catalog.finnish', '''
            '''%(search_index_1)s)'''
        )

    def test_concat(self, User):
        assert str(User.search_index | User.search_index) == (
            '"user".search_index || "user".search_index'
        )

    def test_match_concatenation(self, session, User):
        concat = User.search_index | User.search_index
        bind = session.bind
        assert str(concat.match('something').compile(bind)) == (
            '("user".search_index || "user".search_index) @@ '
            "to_tsquery('pg_catalog.finnish', %(param_1)s)"
        )

    def test_match_with_catalog(self, connection, User):
        expr = User.search_index.match(
            'something',
            postgresql_regconfig='pg_catalog.simple'
        )
        assert str(expr.compile(connection)) == (
            '''"user".search_index @@ to_tsquery('pg_catalog.simple', '''
            '''%(search_index_1)s)'''
        )
