import sqlalchemy as sa
from pytest import raises
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import has_index


class TestHasIndex(object):
    def setup_method(self, method):
        Base = declarative_base()

        class ArticleTranslation(Base):
            __tablename__ = 'article_translation'
            id = sa.Column(sa.Integer, primary_key=True)
            locale = sa.Column(sa.String(10), primary_key=True)
            title = sa.Column(sa.String(100))
            is_published = sa.Column(sa.Boolean, index=True)
            is_deleted = sa.Column(sa.Boolean)
            is_archived = sa.Column(sa.Boolean)

            __table_args__ = (
                sa.Index('my_index', is_deleted, is_archived),
            )

        self.table = ArticleTranslation.__table__

    def test_column_that_belongs_to_an_alias(self):
        alias = sa.orm.aliased(self.table)
        with raises(TypeError):
            assert has_index(alias.c.id)

    def test_compound_primary_key(self):
        assert has_index(self.table.c.id)
        assert not has_index(self.table.c.locale)

    def test_single_column_index(self):
        assert has_index(self.table.c.is_published)

    def test_compound_column_index(self):
        assert has_index(self.table.c.is_deleted)
        assert not has_index(self.table.c.is_archived)
