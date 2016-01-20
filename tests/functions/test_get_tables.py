import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_tables


@pytest.fixture
def TextItem(Base):
    class TextItem(Base):
        __tablename__ = 'text_item'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        type = sa.Column(sa.Unicode(255))

        __mapper_args__ = {
            'polymorphic_on': type,
            'with_polymorphic': '*'
        }
    return TextItem


@pytest.fixture
def Article(TextItem):
    class Article(TextItem):
        __tablename__ = 'article'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
        )
        __mapper_args__ = {
            'polymorphic_identity': u'article'
        }
    return Article


@pytest.fixture
def init_models(TextItem, Article):
    pass


class TestGetTables(object):

    def test_child_class_using_join_table_inheritance(self, TextItem, Article):
        assert get_tables(Article) == [
            TextItem.__table__,
            Article.__table__
        ]

    def test_entity_using_with_polymorphic(self, TextItem, Article):
        assert get_tables(TextItem) == [
            TextItem.__table__,
            Article.__table__
        ]

    def test_instrumented_attribute(self, TextItem):
        assert get_tables(TextItem.name) == [
            TextItem.__table__,
        ]

    def test_polymorphic_instrumented_attribute(self, TextItem, Article):
        assert get_tables(Article.id) == [
            TextItem.__table__,
            Article.__table__
        ]

    def test_column(self, Article):
        assert get_tables(Article.__table__.c.id) == [
            Article.__table__
        ]

    def test_mapper_entity_with_class(self, session, TextItem, Article):
        query = session.query(Article)
        assert get_tables(query._entities[0]) == [
            TextItem.__table__, Article.__table__
        ]

    def test_mapper_entity_with_mapper(self, session, TextItem, Article):
        query = session.query(sa.inspect(Article))
        assert get_tables(query._entities[0]) == [
            TextItem.__table__, Article.__table__
        ]

    def test_column_entity(self, session, TextItem, Article):
        query = session.query(Article.id)
        assert get_tables(query._entities[0]) == [
            TextItem.__table__, Article.__table__
        ]
