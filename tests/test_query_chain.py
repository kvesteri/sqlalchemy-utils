import sqlalchemy as sa
from sqlalchemy_utils import QueryChain

from tests import TestCase


class TestQueryChain(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)

        class BlogPost(self.Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)

        self.User = User
        self.Article = Article
        self.BlogPost = BlogPost

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.users = [
            self.User(),
            self.User()
        ]
        self.articles = [
            self.Article(),
            self.Article(),
            self.Article(),
            self.Article()
        ]
        self.posts = [
            self.BlogPost(),
            self.BlogPost(),
            self.BlogPost(),
        ]

        self.session.add_all(self.users)
        self.session.add_all(self.articles)
        self.session.add_all(self.posts)
        self.session.commit()

        self.chain = QueryChain(
            [
                self.session.query(self.User).order_by('id'),
                self.session.query(self.Article).order_by('id'),
                self.session.query(self.BlogPost).order_by('id')
            ]
        )

    def test_iter(self):
        assert len(list(self.chain)) == 9

    def test_iter_with_limit(self):
        chain = self.chain.limit(4)
        objects = list(chain)
        assert self.users == objects[0:2]
        assert self.articles[0:2] == objects[2:]

    def test_iter_with_offset(self):
        chain = self.chain.offset(3)
        objects = list(chain)
        assert self.articles[1:] + self.posts == objects

    def test_iter_with_limit_and_offset(self):
        chain = self.chain.offset(3).limit(4)
        objects = list(chain)
        assert self.articles[1:] + self.posts[0:1] == objects

    def test_iter_with_offset_spanning_multiple_queries(self):
        chain = self.chain.offset(7)
        objects = list(chain)
        assert self.posts[1:] == objects

    def test_repr(self):
        assert repr(self.chain) == '<QueryChain at 0x%x>' % id(self.chain)

    def test_getitem_with_slice(self):
        chain = self.chain[1:]
        assert chain._offset == 1
        assert chain._limit is None

    def test_getitem_with_single_key(self):
        article = self.chain[2]
        assert article == self.articles[0]
