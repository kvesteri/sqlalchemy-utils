from pytest import raises
import sqlalchemy as sa
from sqlalchemy_utils.types import TSVectorType
from sqlalchemy_utils.expressions import tsvector_match, tsvector_concat
from tests import TestCase


class TSVectorTestCase(TestCase):
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


class TestMatchTSVector(TSVectorTestCase):
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
            'something',
        )) == '(article.search_vector) @@ to_tsquery(:tsvector_match_1)'

    def test_supports_collation_as_3rd_parameter(self):
        assert str(tsvector_match(
            self.Article.search_vector,
            'something',
            'finnish'
        )) == (
            '(article.search_vector) @@ '
            'to_tsquery(:tsvector_match_1, :tsvector_match_2)'
        )


class TestConcatTSVector(TSVectorTestCase):
    def test_concatenate_search_vectors(self):
        assert str(tsvector_match(
            tsvector_concat(
                self.Article.search_vector,
                self.Article.search_vector2
            ),
            'something',
            'finnish'
        )) == (
            '(article.search_vector || article.search_vector2) '
            '@@ to_tsquery(:tsvector_match_1, :tsvector_match_2)'
        )
