import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_type


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
    return User


@pytest.fixture
def Article(Base, User):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)

        author_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
        author = sa.orm.relationship(User)

        some_property = sa.orm.column_property(
            sa.func.coalesce(id, 1)
        )
    return Article


class TestGetType(object):

    def test_instrumented_attribute(self, Article):
        assert isinstance(get_type(Article.id), sa.Integer)

    def test_column_property(self, Article):
        assert isinstance(get_type(Article.id.property), sa.Integer)

    def test_column(self, Article):
        assert isinstance(get_type(Article.__table__.c.id), sa.Integer)

    def test_calculated_column_property(self, Article):
        assert isinstance(get_type(Article.some_property), sa.Integer)

    def test_relationship_property(self, Article, User):
        assert get_type(Article.author) == User

    def test_scalar_select(self, Article):
        query = sa.select([Article.id]).as_scalar()
        assert isinstance(get_type(query), sa.Integer)
