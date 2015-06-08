import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import get_type


class TestGetType(object):
    def setup_method(self, method):
        Base = declarative_base()

        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)

            author_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
            author = sa.orm.relationship(User)

            some_property = sa.orm.column_property(
                sa.func.coalesce(id, 1)
            )

        self.Article = Article
        self.User = User

    def test_instrumented_attribute(self):
        assert isinstance(get_type(self.Article.id), sa.Integer)

    def test_column_property(self):
        assert isinstance(get_type(self.Article.id.property), sa.Integer)

    def test_column(self):
        assert isinstance(get_type(self.Article.__table__.c.id), sa.Integer)

    def test_calculated_column_property(self):
        assert isinstance(get_type(self.Article.some_property), sa.Integer)

    def test_relationship_property(self):
        assert get_type(self.Article.author) == self.User
