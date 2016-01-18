import pytest

from sqlalchemy_utils import analyze


@pytest.mark.usefixtures('postgresql_dsn')
class TestAnalyzeWithPostgres(object):

    def test_runtime(self, session, connection, Article):
        query = session.query(Article)
        assert analyze(connection, query).runtime

    def test_node_types_with_join(self, session, connection, Article):
        query = (
            session.query(Article)
            .join(Article.category)
        )
        analysis = analyze(connection, query)
        assert analysis.node_types == [
            u'Hash Join', u'Seq Scan', u'Hash', u'Seq Scan'
        ]

    def test_node_types_with_index_only_scan(
        self,
        session,
        connection,
        Article
    ):
        query = (
            session.query(Article.name)
            .order_by(Article.name)
            .limit(10)
        )
        analysis = analyze(connection, query)
        assert analysis.node_types == [u'Limit', u'Index Only Scan']
