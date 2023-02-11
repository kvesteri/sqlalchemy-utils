from sqlalchemy.dialects import postgresql

from sqlalchemy_utils.functions import quote


class TestQuote:
    def test_quote_with_preserved_keyword(self, connection, session):
        assert quote(connection, 'order') == '"order"'
        assert quote(session, 'order') == '"order"'
        assert quote(postgresql.dialect(), 'order') == '"order"'

    def test_quote_with_non_preserved_keyword(
        self,
        connection,
        session
    ):
        assert quote(connection, 'some_order') == 'some_order'
        assert quote(session, 'some_order') == 'some_order'
        assert quote(postgresql.dialect(), 'some_order') == 'some_order'
