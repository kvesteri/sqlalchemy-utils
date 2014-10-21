import sqlalchemy as sa

from sqlalchemy_utils import get_tables

from tests import TestCase


class TestGetTables(TestCase):
    def create_models(self):
        class TextItem(self.Base):
            __tablename__ = 'text_item'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            type = sa.Column(sa.Unicode(255))

            __mapper_args__ = {
                'polymorphic_on': type,
                'with_polymorphic': '*'
            }

        class Article(TextItem):
            __tablename__ = 'article'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
            )
            __mapper_args__ = {
                'polymorphic_identity': u'article'
            }

        self.TextItem = TextItem
        self.Article = Article

    def test_child_class_using_join_table_inheritance(self):
        assert get_tables(self.Article) == [
            self.TextItem.__table__,
            self.Article.__table__
        ]

    def test_entity_using_with_polymorphic(self):
        assert get_tables(self.TextItem) == [
            self.TextItem.__table__,
            self.Article.__table__
        ]

    def test_instrumented_attribute(self):
        assert get_tables(self.TextItem.name) == [
            self.TextItem.__table__,
        ]

    def test_polymorphic_instrumented_attribute(self):
        assert get_tables(self.Article.id) == [
            self.TextItem.__table__,
            self.Article.__table__
        ]

    def test_column(self):
        assert get_tables(self.Article.__table__.c.id) == [
            self.Article.__table__
        ]

    def test_mapper_entity_with_class(self):
        query = self.session.query(self.Article)
        assert get_tables(query._entities[0]) == [
            self.TextItem.__table__, self.Article.__table__
        ]

    def test_mapper_entity_with_mapper(self):
        query = self.session.query(sa.inspect(self.Article))
        assert get_tables(query._entities[0]) == [
            self.TextItem.__table__, self.Article.__table__
        ]

    def test_column_entity(self):
        query = self.session.query(self.Article.id)
        assert get_tables(query._entities[0]) == [
            self.TextItem.__table__, self.Article.__table__
        ]
