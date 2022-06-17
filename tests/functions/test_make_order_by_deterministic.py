import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.functions.sort_query import make_order_by_deterministic

from .. import assert_contains


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
        author = sa.orm.relationship('User')
    return Article


@pytest.fixture
def User(Base, Article):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode)
        email = sa.Column(sa.Unicode, unique=True)

        email_lower = sa.orm.column_property(
            sa.func.lower(name)
        )

    User.article_count = sa.orm.column_property(
        sa.select(*_select_args(sa.func.count()))
        .select_from(Article)
        .where(Article.author_id == User.id)
        .label('article_count')
    )
    return User


@pytest.fixture
def init_models(Article, User):
    pass


class TestMakeOrderByDeterministic:

    def test_column_property(self, session, User):
        query = session.query(User).order_by(User.email_lower)
        query = make_order_by_deterministic(query)
        assert_contains('lower(user.name) AS lower_1', query)
        assert_contains('lower_1, user.id ASC', query)

    def test_unique_column(self, session, User):
        query = session.query(User).order_by(User.email)
        query = make_order_by_deterministic(query)

        assert str(query).endswith('ORDER BY user.email')

    def test_non_unique_column(self, session, User):
        query = session.query(User).order_by(User.name)
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY user.name, user.id ASC', query)

    def test_descending_order_by(self, session, User):
        query = session.query(User).order_by(
            sa.desc(User.name)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY user.name DESC, user.id DESC', query)

    def test_ascending_order_by(self, session, User):
        query = session.query(User).order_by(
            sa.asc(User.name)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY user.name ASC, user.id ASC', query)

    def test_string_order_by(self, session, User):
        query = session.query(User).order_by('name')
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY user.name, user.id ASC', query)

    def test_annotated_label(self, session, User):
        query = session.query(User).order_by(User.article_count)
        query = make_order_by_deterministic(query)
        assert_contains('article_count, user.id ASC', query)

    def test_annotated_label_with_descending_order(self, session, User):
        query = session.query(User).order_by(
            sa.desc(User.article_count)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY article_count DESC, user.id DESC', query)

    def test_query_without_order_by(self, session, User):
        query = session.query(User)
        query = make_order_by_deterministic(query)
        assert 'ORDER BY user.id' in str(query)

    def test_alias(self, session, User):
        alias = sa.orm.aliased(User.__table__)
        query = session.query(alias).order_by(alias.c.name)
        query = make_order_by_deterministic(query)
        assert str(query).endswith('ORDER BY user_1.name, user.id ASC')
