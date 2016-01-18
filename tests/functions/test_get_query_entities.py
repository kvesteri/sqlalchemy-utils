import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_query_entities


@pytest.fixture
def TextItem(Base):
    class TextItem(Base):
        __tablename__ = 'text_item'
        id = sa.Column(sa.Integer, primary_key=True)

        type = sa.Column(sa.Unicode(255))

        __mapper_args__ = {
            'polymorphic_on': type,
        }
    return TextItem


@pytest.fixture
def Article(TextItem):
    class Article(TextItem):
        __tablename__ = 'article'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
        )
        category = sa.Column(sa.Unicode(255))
        __mapper_args__ = {
            'polymorphic_identity': u'article'
        }
    return Article


@pytest.fixture
def BlogPost(TextItem):
    class BlogPost(TextItem):
        __tablename__ = 'blog_post'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
        )
        __mapper_args__ = {
            'polymorphic_identity': u'blog_post'
        }
    return BlogPost


@pytest.fixture
def init_models(TextItem, Article, BlogPost):
    pass


class TestGetQueryEntities(object):

    def test_mapper(self, session, TextItem):
        query = session.query(sa.inspect(TextItem))
        assert get_query_entities(query) == [TextItem]

    def test_entity(self, session, TextItem):
        query = session.query(TextItem)
        assert get_query_entities(query) == [TextItem]

    def test_instrumented_attribute(self, session, TextItem):
        query = session.query(TextItem.id)
        assert get_query_entities(query) == [TextItem]

    def test_column(self, session, TextItem):
        query = session.query(TextItem.__table__.c.id)
        assert get_query_entities(query) == [TextItem.__table__]

    def test_aliased_selectable(self, session, TextItem, BlogPost):
        selectable = sa.orm.with_polymorphic(TextItem, [BlogPost])
        query = session.query(selectable)
        assert get_query_entities(query) == [selectable]

    def test_joined_entity(self, session, TextItem, BlogPost):
        query = session.query(TextItem).join(
            BlogPost, BlogPost.id == TextItem.id
        )
        assert get_query_entities(query) == [
            TextItem, sa.inspect(BlogPost)
        ]

    def test_joined_aliased_entity(self, session, TextItem, BlogPost):
        alias = sa.orm.aliased(BlogPost)

        query = session.query(TextItem).join(
            alias, alias.id == TextItem.id
        )
        assert get_query_entities(query) == [TextItem, alias]

    def test_column_entity_with_label(self, session, Article):
        query = session.query(Article.id.label('id'))
        assert get_query_entities(query) == [Article]

    def test_with_subquery(self, session, Article):
        number_of_articles = (
            sa.select(
                [sa.func.count(Article.id)],
            )
            .select_from(
                Article.__table__
            )
        ).label('number_of_articles')

        query = session.query(Article, number_of_articles)
        assert get_query_entities(query) == [
            Article,
            number_of_articles
        ]

    def test_aliased_entity(self, session, Article):
        alias = sa.orm.aliased(Article)
        query = session.query(alias)
        assert get_query_entities(query) == [alias]
