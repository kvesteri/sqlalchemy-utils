import pytest
import sqlalchemy as sa

from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.functions import (
    mock_engine,
    render_expression,
    render_statement
)


class TestRender:

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return User

    @pytest.fixture
    def init_models(self, User):
        pass

    def test_render_orm_query(self, session, User):
        query = session.query(User).filter_by(id=3)
        text = render_statement(query)

        assert 'SELECT user.id, user.name' in text
        assert 'FROM user' in text
        assert 'WHERE user.id = 3' in text

    def test_render_statement(self, session, User):
        statement = User.__table__.select().where(User.id == 3)
        text = render_statement(statement, bind=session.bind)

        assert 'SELECT user.id, user.name' in text
        assert 'FROM user' in text
        assert 'WHERE user.id = 3' in text

    def test_render_statement_without_mapper(self, session):
        statement = sa.select(*_select_args(sa.text('1')))
        text = render_statement(statement, bind=session.bind)

        assert 'SELECT 1' in text

    def test_render_ddl(self, engine, User):
        expression = 'User.__table__.create(engine)'
        stream = render_expression(expression, engine)

        text = stream.getvalue()

        assert 'CREATE TABLE user' in text
        assert 'PRIMARY KEY' in text

    def test_render_mock_ddl(self, engine, User):
        # TODO: mock_engine doesn't seem to work with locally scoped variables.
        self.engine = engine
        with mock_engine('self.engine') as stream:
            User.__table__.create(self.engine)

        text = stream.getvalue()

        assert 'CREATE TABLE user' in text
        assert 'PRIMARY KEY' in text

    def test_render_statement_hangul(self, User, session):
        statement = User.__table__.select().where(
            (User.id == 3)
            & (User.name == "한글")
        )
        text = render_statement(statement, bind=session.bind)

        assert "SELECT user.id, user.name" in text
        assert "FROM user" in text
        assert "user.id = 3" in text
        assert "user.name = '한글'" in text
