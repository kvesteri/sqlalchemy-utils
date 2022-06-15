import pytest
import sqlalchemy as sa

from sqlalchemy_utils import is_loaded


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article_translation'
        id = sa.Column(sa.Integer, primary_key=True)
        title = sa.orm.deferred(sa.Column(sa.String(100)))
    return Article


class TestIsLoaded:

    def test_loaded_property(self, Article):
        article = Article(id=1)
        assert is_loaded(article, 'id')

    def test_unloaded_property(self, Article):
        article = Article(id=4)
        assert not is_loaded(article, 'title')
