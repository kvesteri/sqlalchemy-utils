import sqlalchemy as sa
from sqlalchemy_utils import escape_like
from sqlalchemy_utils.functions import naturally_equivalent
from tests import TestCase
from sqlalchemy_utils.functions import (
    non_indexed_foreign_keys,
    render_statement,
    render_expression,
    mock_engine
)


class TestEscapeLike(TestCase):
    def test_escapes_wildcards(self):
        assert escape_like('_*%') == '*_***%'


class TestNaturallyEquivalent(TestCase):
    def test_returns_true_when_properties_match(self):
        assert naturally_equivalent(
            self.User(name=u'someone'), self.User(name=u'someone')
        )

    def test_skips_primary_keys(self):
        assert naturally_equivalent(
            self.User(id=1, name=u'someone'), self.User(id=2, name=u'someone')
        )


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


class TestRender(TestCase):

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        self.User = User

    def test_render_statement_query(self):
        query = self.session.query(self.User).filter_by(id=3)
        text = render_statement(query)

        assert 'SELECT user.id, user.name' in text
        assert 'FROM user' in text
        assert 'WHERE user.id = 3' in text

    def test_render_statement(self):
        statement = self.User.__table__.select().where(self.User.id == 3)
        text = render_statement(statement, bind=self.session.bind)

        assert 'SELECT user.id, user.name' in text
        assert 'FROM user' in text
        assert 'WHERE user.id = 3' in text

    def test_render_ddl(self):
        context = {'table': self.User.__table__}
        expression = 'table.create(engine)'
        text = render_expression(expression, self.engine, context)

        assert 'CREATE TABLE user' in text
        assert 'PRIMARY KEY' in text

    def test_render_mock_ddl(self):
        with mock_engine('self.engine') as stream:
            self.User.__table__.create(self.engine)

        text = stream.getvalue()

        assert 'CREATE TABLE user' in text
        assert 'PRIMARY KEY' in text
