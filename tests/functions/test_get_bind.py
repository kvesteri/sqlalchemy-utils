from pytest import raises

from sqlalchemy_utils import get_bind
from tests import TestCase


class TestGetBind(TestCase):
    def test_with_session(self):
        assert get_bind(self.session) == self.connection

    def test_with_connection(self):
        assert get_bind(self.connection) == self.connection

    def test_with_model_object(self):
        article = self.Article()
        self.session.add(article)
        assert get_bind(article) == self.connection

    def test_with_unknown_type(self):
        with raises(TypeError):
            get_bind(None)
