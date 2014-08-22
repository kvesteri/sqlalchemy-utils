from sqlalchemy_utils.functions import quote
from tests import TestCase


class TestQuote(TestCase):
    def test_quote_with_preserved_keyword(self):
        assert quote(self.connection, 'order') == '"order"'
        assert quote(self.session, 'order') == '"order"'
        assert quote(self.engine, 'order') == '"order"'

    def test_quote_with_non_preserved_keyword(self):
        assert quote(self.connection, 'some_order') == 'some_order'
        assert quote(self.session, 'some_order') == 'some_order'
        assert quote(self.engine, 'some_order') == 'some_order'
