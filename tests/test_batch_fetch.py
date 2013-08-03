from pytest import raises
from sqlalchemy_utils import batch_fetch
from tests import TestCase


class TestBatchFetch(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        category = self.Category(name=u'Category #1')
        category.articles = [
            self.Article(name=u'Article 1'),
            self.Article(name=u'Article 2')
        ]
        category2 = self.Category(name=u'Category #2')
        category2.articles = [
            self.Article(name=u'Article 3'),
            self.Article(name=u'Article 4'),
            self.Article(name=u'Article 5')
        ]
        self.session.add(category)
        self.session.add(category2)
        self.session.commit()

    def test_raises_error_if_relationship_not_found(self):
        categories = self.session.query(self.Category).all()
        with raises(AttributeError):
            batch_fetch(categories, 'unknown_relation')

    def test_supports_relationship_attributes(self):
        categories = self.session.query(self.Category).all()
        batch_fetch(categories, self.Category.articles)
        query_count = self.connection.query_count
        categories[0].articles  # no lazy load should occur
        assert self.connection.query_count == query_count
