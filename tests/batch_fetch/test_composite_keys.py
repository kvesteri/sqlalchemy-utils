import sqlalchemy as sa
from sqlalchemy_utils import batch_fetch
from tests import TestCase


class TestBatchFetchWithCompositeKeyRelationships(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            author_first_name = sa.Column(
                sa.Unicode(255), sa.ForeignKey(User.first_name)
            )
            author_last_name = sa.Column(
                sa.Unicode(255), sa.ForeignKey(User.last_name)
            )

            author = sa.orm.relationship(
                User,
                primaryjoin=sa.and_(
                    author_first_name == User.first_name,
                    author_last_name == User.last_name
                ),
                backref=sa.orm.backref(
                    'articles'
                )
            )

        self.User = User
        self.Article = Article

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.users = [
            self.User(first_name=u'John', last_name=u'Matrix'),
            self.User(first_name=u'John', last_name=u'The Ripper')
        ]
        articles = [
            self.Article(
                id=1,
                name=u'Article 1',
                author=self.users[0]
            ),
            self.Article(
                id=2,
                name=u'Article 2',
                author=self.users[1]
            ),
            self.Article(
                id=3,
                name=u'Article 3'
            )
        ]
        self.session.add_all(articles)
        self.session.commit()

    def test_supports_relationship_attributes(self):
        articles = self.session.query(self.Article).all()
        batch_fetch(
            articles,
            'author'
        )
        query_count = self.connection.query_count
        assert articles[0].author == self.users[0]  # no lazy load should occur
        assert articles[1].author == self.users[1]  # no lazy load should occur
        assert articles[2].author is None  # no lazy load should occur
        assert self.connection.query_count == query_count
