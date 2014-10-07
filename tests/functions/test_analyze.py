from sqlalchemy_utils import analyze
from tests import TestCase


class TestAnalyzeWithPostgres(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def test_runtime(self):
        query = self.session.query(self.Article)
        assert analyze(self.connection, query).runtime

    def test_node_types_with_join(self):
        query = (
            self.session.query(self.Article)
            .join(self.Article.category)
        )
        analysis = analyze(self.connection, query)
        assert analysis.node_types == [
            u'Hash Join', u'Seq Scan', u'Hash', u'Seq Scan'
        ]

    def test_node_types_with_index_only_scan(self):
        query = (
            self.session.query(self.Article.name)
            .order_by(self.Article.name)
            .limit(10)
        )
        analysis = analyze(self.connection, query)
        assert analysis.node_types == [u'Limit', u'Index Only Scan']
