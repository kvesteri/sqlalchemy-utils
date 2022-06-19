import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy_utils import Asterisk, row_to_json
from sqlalchemy_utils.compat import _declarative_base


@pytest.fixture
def assert_startswith(session):
    def assert_startswith(query, query_part):
        assert str(
            query.compile(dialect=postgresql.dialect())
        ).startswith(query_part)
        # Check that query executes properly
        session.execute(query)
    return assert_startswith


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        content = sa.Column(sa.UnicodeText)
    return Article


class TestAsterisk:
    def test_with_table_object(self):
        Base = _declarative_base()

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)

        assert str(Asterisk(Article.__table__)) == 'article.*'

    def test_with_quoted_identifier(self):
        Base = _declarative_base()

        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

        assert str(Asterisk(User.__table__).compile(
            dialect=postgresql.dialect()
        )) == '"user".*'


class TestRowToJson:
    def test_compiler_with_default_dialect(self):
        assert str(row_to_json(sa.text('article.*'))) == (
            'row_to_json(article.*)'
        )

    def test_compiler_with_postgresql(self):
        assert str(row_to_json(sa.text('article.*')).compile(
            dialect=postgresql.dialect()
        )) == 'row_to_json(article.*)'

    def test_type(self):
        assert isinstance(
            sa.func.row_to_json(sa.text('article.*')).type,
            postgresql.JSON
        )
