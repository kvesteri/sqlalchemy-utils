from pytest import raises
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_utils.expressions import (
    explain,
    explain_analyze,
    tsvector_match,
    tsvector_concat,
    to_tsquery,
    plainto_tsquery
)
from tests import TestCase


class ExpressionTestCase(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            content = sa.Column(sa.UnicodeText)
            search_vector = sa.Column(TSVectorType)
            search_vector2 = sa.Column(TSVectorType)

        self.Article = Article


class TestExplain(ExpressionTestCase):
    def test_render_explain(self):
        assert str(
            explain(self.session.query(self.Article)).compile(
                dialect=postgresql.dialect()
            )
        ).startswith('EXPLAIN SELECT')

    def test_render_explain_with_analyze(self):
        assert str(
            explain(self.session.query(self.Article), analyze=True)
            .compile(
                dialect=postgresql.dialect()
            )
        ).startswith('EXPLAIN ANALYZE SELECT')


class TestExplainAnalyze(ExpressionTestCase):
    def test_render_explain_analyze(self):
        assert str(
            explain_analyze(self.session.query(self.Article))
            .compile(
                dialect=postgresql.dialect()
            )
        ).startswith('EXPLAIN ANALYZE SELECT')


class TestMatchTSVector(ExpressionTestCase):
    def test_raises_exception_if_less_than_2_parameters_given(self):
        with raises(Exception):
            str(
                tsvector_match(
                    self.Article.search_vector,
                )
            )

    def test_supports_postgres(self):
        assert str(tsvector_match(
            self.Article.search_vector,
            to_tsquery('something'),
        )) == '(article.search_vector) @@ to_tsquery(:to_tsquery_1)'


class TestToTSQuery(ExpressionTestCase):
    def test_requires_atleast_one_parameter(self):
        with raises(Exception):
            str(to_tsquery())

    def test_supports_postgres(self):
        assert str(to_tsquery('something')) == 'to_tsquery(:to_tsquery_1)'


class TestPlainToTSQuery(ExpressionTestCase):
    def test_requires_atleast_one_parameter(self):
        with raises(Exception):
            str(plainto_tsquery())

    def test_supports_postgres(self):
        assert str(plainto_tsquery('s')) == (
            'plainto_tsquery(:plainto_tsquery_1)'
        )


class TestConcatTSVector(ExpressionTestCase):
    def test_concatenate_search_vectors(self):
        assert str(tsvector_match(
            tsvector_concat(
                self.Article.search_vector,
                self.Article.search_vector2
            ),
            to_tsquery('finnish', 'something'),
        )) == (
            '(article.search_vector || article.search_vector2) '
            '@@ to_tsquery(:to_tsquery_1, :to_tsquery_2)'
        )
