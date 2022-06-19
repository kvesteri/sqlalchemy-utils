import pytest
import sqlalchemy as sa

from sqlalchemy_utils import QueryChain


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
    return User


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
    return Article


@pytest.fixture
def BlogPost(Base):
    class BlogPost(Base):
        __tablename__ = 'blog_post'
        id = sa.Column(sa.Integer, primary_key=True)
    return BlogPost


@pytest.fixture
def init_models(User, Article, BlogPost):
    pass


@pytest.fixture
def users(session, User):
    users = [User(), User()]
    session.add_all(users)
    session.commit()
    return users


@pytest.fixture
def articles(session, Article):
    articles = [Article(), Article(), Article(), Article()]
    session.add_all(articles)
    session.commit()
    return articles


@pytest.fixture
def posts(session, BlogPost):
    posts = [BlogPost(), BlogPost(), BlogPost()]
    session.add_all(posts)
    session.commit()
    return posts


@pytest.fixture
def chain(session, users, articles, posts, User, Article, BlogPost):
    return QueryChain(
        [
            session.query(User).order_by('id'),
            session.query(Article).order_by('id'),
            session.query(BlogPost).order_by('id')
        ]
    )


class TestQueryChain:

    def test_iter(self, chain):
        assert len(list(chain)) == 9

    def test_iter_with_limit(self, chain, users, articles):
        c = chain.limit(4)
        objects = list(c)
        assert users == objects[0:2]
        assert articles[0:2] == objects[2:]

    def test_iter_with_offset(self, chain, articles, posts):
        c = chain.offset(3)
        objects = list(c)
        assert articles[1:] + posts == objects

    def test_iter_with_limit_and_offset(self, chain, articles, posts):
        c = chain.offset(3).limit(4)
        objects = list(c)
        assert articles[1:] + posts[0:1] == objects

    def test_iter_with_offset_spanning_multiple_queries(self, chain, posts):
        c = chain.offset(7)
        objects = list(c)
        assert posts[1:] == objects

    def test_repr(self, chain):
        assert repr(chain) == '<QueryChain at 0x%x>' % id(chain)

    def test_getitem_with_slice(self, chain):
        c = chain[1:]
        assert c._offset == 1
        assert c._limit is None

    def test_getitem_with_single_key(self, chain, articles):
        article = chain[2]
        assert article == articles[0]

    def test_count(self, chain):
        assert chain.count() == 9
