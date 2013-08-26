import sqlalchemy as sa
from sqlalchemy_utils import batch_fetch, with_backrefs
from tests import TestCase


class TestBatchFetchManyToManyCompositeRelationships(TestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id1 = sa.Column(sa.Integer, primary_key=True)
            id2 = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        article_tag = sa.Table(
            'article_tag',
            self.Base.metadata,
            sa.Column(
                'article_id1',
                sa.Integer,
            ),
            sa.Column(
                'article_id2',
                sa.Integer,
            ),
            sa.Column(
                'tag_id1',
                sa.Integer,
            ),
            sa.Column(
                'tag_id2',
                sa.Integer,
            ),
            sa.ForeignKeyConstraint(
                ['article_id1', 'article_id2'],
                ['article.id1', 'article.id2']
            ),
            sa.ForeignKeyConstraint(
                ['tag_id1', 'tag_id2'],
                ['tag.id1', 'tag.id2']
            )
        )

        class Tag(self.Base):
            __tablename__ = 'tag'
            id1 = sa.Column(sa.Integer, primary_key=True)
            id2 = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            articles = sa.orm.relationship(
                Article,
                secondary=article_tag,
                backref=sa.orm.backref(
                    'tags',
                ),
            )

        self.Article = Article
        self.Tag = Tag

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        articles = [
            self.Article(id1=1, id2=2, name=u'Article 1'),
            self.Article(id1=2, id2=2, name=u'Article 2'),
            self.Article(id1=3, id2=3, name=u'Article 3'),
            self.Article(id1=4, id2=3, name=u'Article 4'),
            self.Article(id1=5, id2=3, name=u'Article 5')
        ]
        self.session.add_all(articles)
        self.session.flush()

        tags = [
            self.Tag(id1=1, id2=2, name=u'Tag 1'),
            self.Tag(id1=2, id2=3, name=u'Tag 2'),
            self.Tag(id1=3, id2=4, name=u'Tag 3')
        ]
        articles[0].tags = tags
        articles[3].tags = tags[1:]
        self.session.commit()

    def test_deep_relationships(self):
        articles = (
            self.session.query(self.Article)
            .order_by(self.Article.id1).all()
        )
        batch_fetch(
            articles,
            'tags'
        )
        query_count = self.connection.query_count
        assert articles[0].tags
        articles[1].tags
        assert articles[3].tags
        assert self.connection.query_count == query_count

    def test_many_to_many_backref_population(self):
        articles = (
            self.session.query(self.Article)
            .order_by(self.Article.id1).all()
        )
        batch_fetch(
            articles,
            with_backrefs('tags'),
        )
        query_count = self.connection.query_count
        tags = articles[0].tags
        tags2 = articles[3].tags
        tags[0].articles
        tags2[0].articles
        names = [article.name for article in tags[0].articles]
        assert u'Article 1' in names
        assert self.connection.query_count == query_count
