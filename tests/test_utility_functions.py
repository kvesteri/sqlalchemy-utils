import sqlalchemy as sa
from sqlalchemy_utils import escape_like, defer_except
from tests import TestCase
from sqlalchemy_utils.functions import (
    non_indexed_foreign_keys,
    render_statement,
)


class TestEscapeLike(TestCase):
    def test_escapes_wildcards(self):
        assert escape_like('_*%') == '*_***%'


class TestDeferExcept(TestCase):
    def test_deferred_loads_all_columns_except_the_ones_given(self):
        query = self.session.query(self.Article)
        query = defer_except(query, ['id'])
        assert str(query) == 'SELECT article.id AS article_id \nFROM article'


class TestFindNonIndexedForeignKeys(TestCase):
    # dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

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
            author_id = sa.Column(
                sa.Integer, sa.ForeignKey(User.id), index=True
            )
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category,
                primaryjoin=category_id == Category.id,
                backref=sa.orm.backref(
                    'articles',
                )
            )

        self.User = User
        self.Category = Category
        self.Article = Article

    def test_finds_all_non_indexed_fks(self):
        fks = non_indexed_foreign_keys(self.Base.metadata, self.engine)
        assert (
            'article' in
            fks
        )
        column_names = [
            column_name for column_name in fks['article'][0].columns
        ]
        assert 'category_id' in column_names
        assert 'author_id' not in column_names

    def test_render_statement_query(self):
        query = self.session.query(self.User).filter_by(id=3)
        render = render_statement(query)

        assert 'SELECT user.id, user.name' in render
        assert 'FROM user' in render
        assert 'WHERE user.id = 3' in render

    def test_render_statement(self):
        statement = self.User.__table__.select().where(self.User.id == 3)
        render = render_statement(statement, bind=self.session.bind)

        assert 'SELECT user.id, user.name' in render
        assert 'FROM user' in render
        assert 'WHERE user.id = 3' in render
