from sqlalchemy_utils import defer_except
from tests import TestCase


class TestDeferExcept(TestCase):
    def test_supports_properties_as_strings(self):
        query = self.session.query(self.Article)
        query = defer_except(query, ['id'])
        assert str(query) == 'SELECT article.id AS article_id \nFROM article'
