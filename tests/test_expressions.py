import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy_utils import Asterisk, row_to_json
from sqlalchemy_utils.expressions import explain, explain_analyze


@pytest.fixture
def assert_startswith(session):
    def assert_startswith(query, query_part):
        assert str(
            query.compile(dialect=postgresql.dialect())
        ).startswith(query_part)
        # Check that query executes properly
        session.execute(query)
    return assert_startswith


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
    return Article


@pytest.mark.usefixtures('postgresql_dsn')
class TestExplain(object):

    def test_render_explain(self, session, assert_startswith, Article):
        assert_startswith(
            explain(session.query(Article)),
            'EXPLAIN SELECT'
        )

    def test_render_explain_with_analyze(
        self,
        session,
        assert_startswith,
        Article
    ):
        assert_startswith(
            explain(session.query(Article), analyze=True),
            'EXPLAIN (ANALYZE true) SELECT'
        )

    def test_with_string_as_stmt_param(self, assert_startswith):
        assert_startswith(
            explain('SELECT 1 FROM article'),
            'EXPLAIN SELECT'
        )

    def test_format(self, assert_startswith):
        assert_startswith(
            explain('SELECT 1 FROM article', format='json'),
            'EXPLAIN (FORMAT json) SELECT'
        )

    def test_timing(self, assert_startswith):
        assert_startswith(
            explain('SELECT 1 FROM article', analyze=True, timing=False),
            'EXPLAIN (ANALYZE true, TIMING false) SELECT'
        )

    def test_verbose(self, assert_startswith):
        assert_startswith(
            explain('SELECT 1 FROM article', verbose=True),
            'EXPLAIN (VERBOSE true) SELECT'
        )

    def test_buffers(self, assert_startswith):
        assert_startswith(
            explain('SELECT 1 FROM article', analyze=True, buffers=True),
            'EXPLAIN (ANALYZE true, BUFFERS true) SELECT'
        )

    def test_costs(self, assert_startswith):
        assert_startswith(
            explain('SELECT 1 FROM article', costs=False),
            'EXPLAIN (COSTS false) SELECT'
        )


class TestExplainAnalyze(object):
    def test_render_explain_analyze(self, session, Article):
        assert str(
            explain_analyze(session.query(Article))
            .compile(
                dialect=postgresql.dialect()
            )
        ).startswith('EXPLAIN (ANALYZE true) SELECT')


class TestAsterisk(object):
    def test_with_table_object(self):
        Base = sa.ext.declarative.declarative_base()

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)

        assert str(Asterisk(Article.__table__)) == 'article.*'

    def test_with_quoted_identifier(self):
        Base = sa.ext.declarative.declarative_base()

        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

        assert str(Asterisk(User.__table__).compile(
            dialect=postgresql.dialect()
        )) == '"user".*'


class TestRowToJson(object):
    def test_compiler_with_default_dialect(self):
        with pytest.raises(sa.exc.CompileError):
            str(row_to_json(sa.text('article.*')))

    def test_compiler_with_postgresql(self):
        assert str(row_to_json(sa.text('article.*')).compile(
            dialect=postgresql.dialect()
        )) == 'row_to_json(article.*)'

    def test_type(self):
        assert isinstance(
            sa.func.row_to_json(sa.text('article.*')).type,
            postgresql.JSON
        )


class TestArrayAgg(object):
    def test_compiler_with_default_dialect(self):
        with pytest.raises(sa.exc.CompileError):
            str(sa.func.array_agg(sa.text('u.name')))

    def test_compiler_with_postgresql(self):
        assert str(sa.func.array_agg(sa.text('u.name')).compile(
            dialect=postgresql.dialect()
        )) == "array_agg(u.name)"

    def test_type(self):
        assert isinstance(
            sa.func.array_agg(sa.text('u.name')).type,
            postgresql.ARRAY
        )

    def test_array_agg_with_default(self):
        Base = sa.ext.declarative.declarative_base()

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)

        assert str(sa.func.array_agg(Article.id, [1]).compile(
            dialect=postgresql.dialect()
        )) == (
            'coalesce(array_agg(article.id), CAST(ARRAY[%(param_1)s]'
            ' AS INTEGER[]))'
        )
