import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import is_loaded


class TestIsLoaded(object):
    def setup_method(self, method):
        Base = declarative_base()

        class Article(Base):
            __tablename__ = 'article_translation'
            id = sa.Column(sa.Integer, primary_key=True)
            title = sa.orm.deferred(sa.Column(sa.String(100)))

        self.Article = Article

    def test_loaded_property(self):
        article = self.Article(id=1)
        assert is_loaded(article, 'id')

    def test_unloaded_property(self):
        article = self.Article(id=4)
        assert not is_loaded(article, 'title')
