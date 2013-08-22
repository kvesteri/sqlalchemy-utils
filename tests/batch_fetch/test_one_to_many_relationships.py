import sqlalchemy as sa
from pytest import raises
from sqlalchemy_utils import batch_fetch
from tests import TestCase


class TestBatchFetchOneToManyRelationships(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category,
                primaryjoin=category_id == Category.id,
                backref=sa.orm.backref(
                    'articles'
                )
            )

        self.User = User
        self.Category = Category
        self.Article = Article

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        articles = [
            self.Article(name=u'Article 1'),
            self.Article(name=u'Article 2'),
            self.Article(name=u'Article 3'),
            self.Article(name=u'Article 4'),
            self.Article(name=u'Article 5')
        ]
        self.session.add_all(articles)
        self.session.flush()

        category = self.Category(name=u'Category #1')
        category.articles = articles[0:2]
        category2 = self.Category(name=u'Category #2')
        category2.articles = articles[2:]
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
        articles = categories[0].articles  # no lazy load should occur
        assert len(articles) == 2
        article_names = [article.name for article in articles]

        assert 'Article 1' in article_names
        assert 'Article 2' in article_names
        articles = categories[1].articles  # no lazy load should occur
        assert len(articles) == 3
        article_names = [article.name for article in articles]
        assert 'Article 3' in article_names
        assert 'Article 4' in article_names
        assert 'Article 5' in article_names
        assert self.connection.query_count == query_count
