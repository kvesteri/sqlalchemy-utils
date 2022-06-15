import pytest
import sqlalchemy as sa

from sqlalchemy_utils import has_changes


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article_translation'
        id = sa.Column(sa.Integer, primary_key=True)
        title = sa.Column(sa.String(100))
    return Article


class TestHasChangesWithStringAttr:
    def test_without_changed_attr(self, Article):
        article = Article()
        assert not has_changes(article, 'title')

    def test_with_changed_attr(self, Article):
        article = Article(title='Some title')
        assert has_changes(article, 'title')


class TestHasChangesWithMultipleAttrs:
    def test_without_changed_attr(self, Article):
        article = Article()
        assert not has_changes(article, ['title'])

    def test_with_changed_attr(self, Article):
        article = Article(title='Some title')
        assert has_changes(article, ['title', 'id'])


class TestHasChangesWithExclude:
    def test_without_changed_attr(self, Article):
        article = Article()
        assert not has_changes(article, exclude=['id'])

    def test_with_changed_attr(self, Article):
        article = Article(title='Some title')
        assert has_changes(article, exclude=['id'])
        assert not has_changes(article, exclude=['title'])
