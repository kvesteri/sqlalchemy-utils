import sqlalchemy as sa
from tests import TestCase
from sqlalchemy_utils.functions import (
    render_statement,
    render_expression,
    mock_engine
)


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
        expression = 'self.User.__table__.create(engine)'
        stream = render_expression(expression, self.engine)

        text = stream.getvalue()

        assert 'CREATE TABLE user' in text
        assert 'PRIMARY KEY' in text

    def test_render_mock_ddl(self):
        with mock_engine('self.engine') as stream:
            self.User.__table__.create(self.engine)

        text = stream.getvalue()

        assert 'CREATE TABLE user' in text
        assert 'PRIMARY KEY' in text
