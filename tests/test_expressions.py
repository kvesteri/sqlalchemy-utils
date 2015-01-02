import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.expressions import explain, explain_analyze
from tests import TestCase


class ExpressionTestCase(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            content = sa.Column(sa.UnicodeText)

        self.Article = Article

    def assert_startswith(self, query, query_part):
        assert str(
            query.compile(dialect=postgresql.dialect())
        ).startswith(query_part)
        # Check that query executes properly
        self.session.execute(query)


class TestExplain(ExpressionTestCase):
    def test_render_explain(self):
        self.assert_startswith(
            explain(self.session.query(self.Article)),
            'EXPLAIN SELECT'
        )

    def test_render_explain_with_analyze(self):
        self.assert_startswith(
            explain(self.session.query(self.Article), analyze=True),
            'EXPLAIN (ANALYZE true) SELECT'
        )

    def test_with_string_as_stmt_param(self):
        self.assert_startswith(
            explain('SELECT 1 FROM article'),
            'EXPLAIN SELECT'
        )

    def test_format(self):
        self.assert_startswith(
            explain('SELECT 1 FROM article', format='json'),
            'EXPLAIN (FORMAT json) SELECT'
        )

    def test_timing(self):
        self.assert_startswith(
            explain('SELECT 1 FROM article', analyze=True, timing=False),
            'EXPLAIN (ANALYZE true, TIMING false) SELECT'
        )

    def test_verbose(self):
        self.assert_startswith(
            explain('SELECT 1 FROM article', verbose=True),
            'EXPLAIN (VERBOSE true) SELECT'
        )

    def test_buffers(self):
        self.assert_startswith(
            explain('SELECT 1 FROM article', analyze=True, buffers=True),
            'EXPLAIN (ANALYZE true, BUFFERS true) SELECT'
        )

    def test_costs(self):
        self.assert_startswith(
            explain('SELECT 1 FROM article', costs=False),
            'EXPLAIN (COSTS false) SELECT'
        )


class TestExplainAnalyze(ExpressionTestCase):
    def test_render_explain_analyze(self):
        assert str(
            explain_analyze(self.session.query(self.Article))
            .compile(
                dialect=postgresql.dialect()
            )
        ).startswith('EXPLAIN (ANALYZE true) SELECT')
