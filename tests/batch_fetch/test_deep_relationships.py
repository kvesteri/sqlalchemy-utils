import sqlalchemy as sa
from sqlalchemy_utils import batch_fetch, with_backrefs
from tests import TestCase


class TestBatchFetchDeepRelationships(TestCase):
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

        article_tag = sa.Table(
            'article_tag',
            self.Base.metadata,
            sa.Column(
                'article_id',
                sa.Integer,
                sa.ForeignKey('article.id', ondelete='cascade')
            ),
            sa.Column(
                'tag_id',
                sa.Integer,
                sa.ForeignKey('tag.id', ondelete='cascade')
            )
        )

        class Tag(self.Base):
            __tablename__ = 'tag'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            articles = sa.orm.relationship(
                Article,
                secondary=article_tag,
                backref=sa.orm.backref(
                    'tags'
                )
            )

        self.User = User
        self.Category = Category
        self.Article = Article
        self.Tag = Tag

    def init_data(self):
        articles = [
            self.Article(name=u'Article 1'),
            self.Article(name=u'Article 2'),
            self.Article(name=u'Article 3'),
            self.Article(name=u'Article 4'),
            self.Article(name=u'Article 5')
        ]
        self.session.add_all(articles)
        self.session.flush()

        tags = [
            self.Tag(name=u'Tag 1'),
            self.Tag(name=u'Tag 2'),
            self.Tag(name=u'Tag 3')
        ]
        articles[0].tags = tags
        articles[3].tags = tags[1:]

        category = self.Category(name=u'Category #1')
        category.articles = articles[0:2]
        category2 = self.Category(name=u'Category #2')
        category2.articles = articles[2:]
        self.session.add(category)
        self.session.add(category2)
        self.session.commit()

    def test_supports_empty_related_entities(self):
        category = self.Category(name=u'Category #1')
        self.session.add(category)
        self.session.commit()
        categories = self.session.query(self.Category).all()
        batch_fetch(
            categories,
            'articles',
            'articles.tags'
        )
        query_count = self.connection.query_count
        assert not categories[0].articles
        assert self.connection.query_count == query_count

    def test_deep_relationships(self):
        self.init_data()
        categories = self.session.query(self.Category).all()
        batch_fetch(
            categories,
            'articles',
            'articles.tags'
        )
        query_count = self.connection.query_count
        categories[0].articles[0].tags
        assert self.connection.query_count == query_count
        categories[1].articles[1].tags
        assert self.connection.query_count == query_count

    def test_many_to_many_backref_population(self):
        self.init_data()
        categories = self.session.query(self.Category).all()
        batch_fetch(
            categories,
            'articles',
            with_backrefs('articles.tags'),
        )
        query_count = self.connection.query_count
        tags = categories[0].articles[0].tags
        tags2 = categories[1].articles[1].tags
        tags[0].articles
        tags2[0].articles
        names = [article.name for article in tags[0].articles]
        assert u'Article 1' in names
        assert self.connection.query_count == query_count
