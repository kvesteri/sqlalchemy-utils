import pytest
import sqlalchemy as sa

from sqlalchemy_utils import sort_query
from sqlalchemy_utils.functions import QuerySorterException

from . import assert_contains


class TestSortQuery(object):
    def test_without_sort_param_returns_the_query_object_untouched(
        self,
        session,
        Article
    ):
        query = session.query(Article)
        query = sort_query(query, '')
        assert query == query

    def test_column_ascending(self, session, Article):
        query = sort_query(session.query(Article), 'name')
        assert_contains('ORDER BY article.name ASC', query)

    def test_column_descending(self, session, Article):
        query = sort_query(session.query(Article), '-name')
        assert_contains('ORDER BY article.name DESC', query)

    def test_skips_unknown_columns(self, session, Article):
        query = session.query(Article)
        query = sort_query(query, '-unknown')
        assert query == query

    def test_non_silent_mode(self, session, Article):
        query = session.query(Article)
        with pytest.raises(QuerySorterException):
            sort_query(query, '-unknown', silent=False)

    def test_join(self, session, Article):
        query = (
            session.query(Article)
            .join(Article.category)
        )
        query = sort_query(query, 'name', silent=False)
        assert_contains('ORDER BY article.name ASC', query)

    def test_calculated_value_ascending(self, session, Article, Category):
        query = session.query(
            Category, sa.func.count(Article.id).label('articles')
        )
        query = sort_query(query, 'articles')
        assert_contains('ORDER BY articles ASC', query)

    def test_calculated_value_descending(self, session, Article, Category):
        query = session.query(
            Category, sa.func.count(Article.id).label('articles')
        )
        query = sort_query(query, '-articles')
        assert_contains('ORDER BY articles DESC', query)

    def test_subqueried_scalar(self, session, Article, Category):
        article_count = (
            sa.sql.select(
                [sa.func.count(Article.id)],
                from_obj=[Article.__table__]
            )
            .where(Article.category_id == Category.id)
            .correlate(Category.__table__)
        )

        query = session.query(
            Category, article_count.label('articles')
        )
        query = sort_query(query, '-articles')
        assert_contains('ORDER BY articles DESC', query)

    def test_aliased_joined_entity(self, session, Article, Category):
        alias = sa.orm.aliased(Category, name='categories')
        query = session.query(
            Article
        ).join(
            alias, Article.category
        )
        query = sort_query(query, '-categories-name')
        assert_contains('ORDER BY categories.name DESC', query)

    def test_joined_table_column(self, session, Article):
        query = session.query(Article).join(Article.category)
        query = sort_query(query, 'category-name')
        assert_contains('category.name ASC', query)

    def test_multiple_columns(self, session, Article):
        query = session.query(Article)
        query = sort_query(query, 'name', 'id')
        assert_contains('article.name ASC, article.id ASC', query)

    def test_column_property(self, session, Article, Category):
        Category.article_count = sa.orm.column_property(
            sa.select([sa.func.count(Article.id)])
            .where(Article.category_id == Category.id)
            .label('article_count')
        )

        query = session.query(Category)
        query = sort_query(query, 'article_count')
        assert_contains('article_count ASC', query)

    def test_column_property_descending(self, session, Article, Category):
        Category.article_count = sa.orm.column_property(
            sa.select([sa.func.count(Article.id)])
            .where(Article.category_id == Category.id)
            .label('article_count')
        )

        query = session.query(Category)
        query = sort_query(query, '-article_count')
        assert_contains('article_count DESC', query)

    def test_relationship_property(self, session, Category):
        query = session.query(Category)
        query = sort_query(query, 'articles')
        assert 'ORDER BY' not in str(query)

    def test_regular_property(self, session, Category):
        query = session.query(Category)
        query = sort_query(query, 'name_alias')
        assert 'ORDER BY' not in str(query)

    def test_synonym_property(self, session, Category):
        query = session.query(Category)
        query = sort_query(query, 'name_synonym')
        assert_contains('ORDER BY category.name ASC', query)

    def test_hybrid_property(self, session, Category):
        query = session.query(Category)
        query = sort_query(query, 'articles_count')
        assert_contains('ORDER BY (SELECT count(article.id) AS count_1', query)

    def test_hybrid_property_descending(self, session, Category):
        query = session.query(Category)
        query = sort_query(query, '-articles_count')
        assert_contains(
            'ORDER BY (SELECT count(article.id) AS count_1',
            query
        )
        assert ' DESC' in str(query)

    def test_assigned_hybrid_property(self, session, Article):
        def getter(self):
            return self.name

        Article.some_hybrid = sa.ext.hybrid.hybrid_property(
            fget=getter
        )
        query = session.query(Article)
        query = sort_query(query, 'some_hybrid')
        assert_contains('ORDER BY article.name ASC', query)

    def test_with_mapper_and_column_property(self, session, Base, Article):
        class Apple(Base):
            __tablename__ = 'apple'
            id = sa.Column(sa.Integer, primary_key=True)
            article_id = sa.Column(sa.Integer, sa.ForeignKey(Article.id))

        Article.apples = sa.orm.relationship(Apple)

        Article.apple_count = sa.orm.column_property(
            sa.select([sa.func.count(Apple.id)])
            .where(Apple.article_id == Article.id)
            .correlate(Article.__table__)
            .label('apple_count'),
            deferred=True
        )
        query = (
            session.query(sa.inspect(Article))
            .outerjoin(Article.apples)
            .options(
                sa.orm.undefer(Article.apple_count)
            )
            .options(sa.orm.contains_eager(Article.apples))
        )
        query = sort_query(query, 'apple_count')
        assert 'ORDER BY apple_count' in str(query)

    def test_table(self, session, Article):
        query = session.query(Article.__table__)
        query = sort_query(query, 'name')
        assert_contains('ORDER BY article.name', query)


@pytest.mark.usefixtures('postgresql_dsn')
class TestSortQueryRelationshipCounts(object):
    """
    Currently this doesn't work with SQLite
    """

    def test_relation_hybrid_property(self, session, Article):
        query = (
            session.query(Article)
            .join(Article.category)
        ).group_by(Article.id)
        query = sort_query(query, '-category-articles_count')
        assert_contains('ORDER BY (SELECT count(article.id) AS count_1', query)

    def test_aliased_hybrid_property(self, session, Article, Category):
        alias = sa.orm.aliased(
            Category,
            name='categories'
        )
        query = (
            session.query(Article)
            .outerjoin(alias, Article.category)
            .options(
                sa.orm.contains_eager(Article.category, alias=alias)
            )
        ).group_by(alias.id, Article.id)
        query = sort_query(query, '-categories-articles_count')
        assert_contains('ORDER BY (SELECT count(article.id) AS count_1', query)

    def test_aliased_concat_hybrid_property(self, session, Article, Category):
        alias = sa.orm.aliased(
            Category,
            name='aliased'
        )
        query = (
            session.query(Article)
            .outerjoin(alias, Article.category)
            .options(
                sa.orm.contains_eager(Article.category, alias=alias)
            )
        )
        query = sort_query(query, 'aliased-full_name')
        assert_contains(
            'concat(aliased.title, %(concat_1)s, aliased.name)', query
        )


@pytest.mark.usefixtures('postgresql_dsn')
class TestSortQueryWithPolymorphicInheritance(object):
    """
    Currently this doesn't work with SQLite
    """

    @pytest.fixture
    def TextItem(self, Base):
        class TextItem(Base):
            __tablename__ = 'text_item'
            id = sa.Column(sa.Integer, primary_key=True)

            type = sa.Column(sa.Unicode(255))

            __mapper_args__ = {
                'polymorphic_on': type,
                'with_polymorphic': '*'
            }
        return TextItem

    @pytest.fixture
    def Article(self, TextItem):
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
    def init_models(self, TextItem, Article):
        pass

    def test_column_property(self, session, TextItem):
        TextItem.item_count = sa.orm.column_property(
            sa.select(
                [
                    sa.func.count('1')
                ],
            )
            .select_from(TextItem.__table__)
            .label('item_count')
        )

        query = sort_query(
            session.query(TextItem),
            'item_count'
        )
        assert_contains('ORDER BY item_count', query)

    def test_child_class_attribute(self, session, TextItem):
        query = sort_query(
            session.query(TextItem),
            'category'
        )
        assert_contains('ORDER BY article.category ASC', query)

    def test_with_ambiguous_column(self, session, TextItem):
        query = sort_query(
            session.query(TextItem),
            'id'
        )
        assert_contains('ORDER BY text_item.id ASC', query)


@pytest.mark.usefixtures('postgresql_dsn')
class TestSortQueryWithCustomPolymorphic(object):
    """
    Currently this doesn't work with SQLite
    """

    @pytest.fixture
    def TextItem(self, Base):
        class TextItem(Base):
            __tablename__ = 'text_item'
            id = sa.Column(sa.Integer, primary_key=True)

            type = sa.Column(sa.Unicode(255))

            __mapper_args__ = {
                'polymorphic_on': type,
            }
        return TextItem

    @pytest.fixture
    def Article(self, TextItem):
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
    def BlogPost(self, TextItem):
        class BlogPost(TextItem):
            __tablename__ = 'blog_post'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
            )
            __mapper_args__ = {
                'polymorphic_identity': u'blog_post'
            }
        return BlogPost

    def test_with_unknown_column(self, session, TextItem, BlogPost):
        query = sort_query(
            session.query(
                sa.orm.with_polymorphic(TextItem, [BlogPost])
            ),
            'category'
        )
        assert 'ORDER BY' not in str(query)

    def test_with_existing_column(self, session, TextItem, Article):
        query = sort_query(
            session.query(
                sa.orm.with_polymorphic(TextItem, [Article])
            ),
            'category'
        )
        assert 'ORDER BY' in str(query)
