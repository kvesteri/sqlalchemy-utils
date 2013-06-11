from sqlalchemy_utils import escape_like, defer_except
from tests import TestCase


class TestEscapeLike(TestCase):
    def test_escapes_wildcards(self):
        assert escape_like('_*%') == '*_***%'


class TestDeferExcept(TestCase):
    def test_deferred_loads_all_columns_except_the_ones_given(self):
        query = self.session.query(self.Article)
        query = defer_except(query, ['id'])
        assert str(query) == 'SELECT article.id AS article_id \nFROM article'
