import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import has_any_changes


class TestHasAnyChanges(object):
    def setup_method(self, method):
        Base = declarative_base()

        class Article(Base):
            __tablename__ = 'article_translation'
            id = sa.Column(sa.Integer, primary_key=True)
            title = sa.Column(sa.String(100))

        self.Article = Article

    def test_without_changed_attr(self):
        article = self.Article()
        assert not has_any_changes(article, ['title'])

    def test_with_changed_attr(self):
        article = self.Article(title='Some title')
        assert has_any_changes(article, ['title', 'id'])
