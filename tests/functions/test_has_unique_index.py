from pytest import raises
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import has_unique_index


class TestHasUniqueIndex(object):
    def setup_method(self, method):
        Base = declarative_base()

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)

        class ArticleTranslation(Base):
            __tablename__ = 'article_translation'
            id = sa.Column(sa.Integer, primary_key=True)
            locale = sa.Column(sa.String(10), primary_key=True)
            title = sa.Column(sa.String(100))
            is_published = sa.Column(sa.Boolean, index=True)
            is_deleted = sa.Column(sa.Boolean, unique=True)
            is_archived = sa.Column(sa.Boolean)

            __table_args__ = (
                sa.Index('my_index', is_archived, is_published, unique=True),
            )

        self.articles = Article.__table__
        self.article_translations = ArticleTranslation.__table__

    def test_primary_key(self):
        assert has_unique_index(self.articles.c.id)

    def test_column_of_aliased_table(self):
        alias = sa.orm.aliased(self.articles)
        with raises(TypeError):
            assert has_unique_index(alias.c.id)

    def test_unique_index(self):
        assert has_unique_index(self.article_translations.c.is_deleted)

    def test_compound_primary_key(self):
        assert not has_unique_index(self.article_translations.c.id)
        assert not has_unique_index(self.article_translations.c.locale)

    def test_single_column_index(self):
        assert not has_unique_index(self.article_translations.c.is_published)

    def test_compound_column_unique_index(self):
        assert not has_unique_index(self.article_translations.c.is_published)
        assert not has_unique_index(self.article_translations.c.is_archived)
