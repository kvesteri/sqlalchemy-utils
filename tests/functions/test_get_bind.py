import pytest

from sqlalchemy_utils import get_bind


class TestGetBind:
    def test_with_session(self, session, connection):
        assert get_bind(session) == connection

    def test_with_connection(self, session, connection):
        assert get_bind(connection) == connection

    def test_with_model_object(self, session, connection, Article):
        article = Article()
        session.add(article)
        assert get_bind(article) == connection

    def test_with_unknown_type(self):
        with pytest.raises(TypeError):
            get_bind(None)
