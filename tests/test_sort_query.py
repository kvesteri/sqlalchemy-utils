import sqlalchemy as sa
from pytest import raises
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy_utils import sort_query
from sqlalchemy_utils.functions import QuerySorterException
from tests import assert_contains, TestCase


class TestSortQuery(TestCase):
    def test_without_sort_param_returns_the_query_object_untouched(self):
        query = self.session.query(self.Article)
        query = sort_query(query, '')
        assert query == query

    def test_column_ascending(self):
        query = sort_query(self.session.query(self.Article), 'name')
        assert_contains('ORDER BY article.name ASC', query)

    def test_column_descending(self):
        query = sort_query(self.session.query(self.Article), '-name')
        assert_contains('ORDER BY article.name DESC', query)

    def test_skips_unknown_columns(self):
        query = self.session.query(self.Article)
        query = sort_query(query, '-unknown')
        assert query == query

    def test_non_silent_mode(self):
        query = self.session.query(self.Article)
        with raises(QuerySorterException):
            sort_query(query, '-unknown', silent=False)

    def test_join(self):
        query = (
            self.session.query(self.Article)
            .join(self.Article.category)
        )
        query = sort_query(query, 'name', silent=False)
        assert_contains('ORDER BY article.name ASC', query)

    def test_calculated_value_ascending(self):
        query = self.session.query(
            self.Category, sa.func.count(self.Article.id).label('articles')
        )
        query = sort_query(query, 'articles')
        assert_contains('ORDER BY articles ASC', query)

    def test_calculated_value_descending(self):
        query = self.session.query(
            self.Category, sa.func.count(self.Article.id).label('articles')
        )
        query = sort_query(query, '-articles')
        assert_contains('ORDER BY articles DESC', query)

    def test_subqueried_scalar(self):
        article_count = (
            sa.sql.select(
                [sa.func.count(self.Article.id)],
                from_obj=[self.Article.__table__]
            )
            .where(self.Article.category_id == self.Category.id)
            .correlate(self.Category.__table__)
        )

        query = self.session.query(
            self.Category, article_count.label('articles')
        )
        query = sort_query(query, '-articles')
        assert_contains('ORDER BY articles DESC', query)

    def test_aliased_joined_entity(self):
        alias = sa.orm.aliased(self.Category, name='categories')
        query = self.session.query(
            self.Article
        ).join(
            alias, self.Article.category
        )
        query = sort_query(query, '-categories-name')
        assert_contains('ORDER BY categories.name DESC', query)

    def test_joined_table_column(self):
        query = self.session.query(self.Article).join(self.Article.category)
        query = sort_query(query, 'category-name')
        assert_contains('category.name ASC', query)

    def test_multiple_columns(self):
        query = self.session.query(self.Article)
        query = sort_query(query, 'name', 'id')
        assert_contains('article.name ASC, article.id ASC', query)

    def test_column_property(self):
        self.Category.article_count = sa.orm.column_property(
            sa.select([sa.func.count(self.Article.id)])
            .where(self.Article.category_id == self.Category.id)
            .label('article_count')
        )

        query = self.session.query(self.Category)
        query = sort_query(query, 'article_count')
        assert_contains('article_count ASC', query)

    def test_column_property_descending(self):
        self.Category.article_count = sa.orm.column_property(
            sa.select([sa.func.count(self.Article.id)])
            .where(self.Article.category_id == self.Category.id)
            .label('article_count')
        )

        query = self.session.query(self.Category)
        query = sort_query(query, '-article_count')
        assert_contains('article_count DESC', query)

    def test_relationship_property(self):
        query = self.session.query(self.Category)
        query = sort_query(query, 'articles')
        assert 'ORDER BY' not in str(query)

    def test_regular_property(self):
        query = self.session.query(self.Category)
        query = sort_query(query, 'name_alias')
        assert 'ORDER BY' not in str(query)

    def test_synonym_property(self):
        query = self.session.query(self.Category)
        query = sort_query(query, 'name_synonym')
        assert_contains('ORDER BY category.name ASC', query)

    def test_hybrid_property(self):
        query = self.session.query(self.Category)
        query = sort_query(query, 'articles_count')
        assert_contains('ORDER BY (SELECT count(article.id) AS count_1', query)

    def test_hybrid_property_descending(self):
        query = self.session.query(self.Category)
        query = sort_query(query, '-articles_count')
        assert_contains(
            'ORDER BY (SELECT count(article.id) AS count_1',
            query
        )
        assert ' DESC' in str(query)

    def test_assigned_hybrid_property(self):
        def getter(self):
            return self.name

        self.Article.some_hybrid = sa.ext.hybrid.hybrid_property(
            fget=getter
        )
        query = self.session.query(self.Article)
        query = sort_query(query, 'some_hybrid')
        assert_contains('ORDER BY article.name ASC', query)

    def test_with_mapper_and_column_property(self):
        class Apple(self.Base):
            __tablename__ = 'apple'
            id = sa.Column(sa.Integer, primary_key=True)
            article_id = sa.Column(sa.Integer, sa.ForeignKey(self.Article.id))

        self.Article.apples = sa.orm.relationship(Apple)

        self.Article.apple_count = sa.orm.column_property(
            sa.select([sa.func.count(Apple.id)])
            .where(Apple.article_id == self.Article.id)
            .correlate(self.Article.__table__)
            .label('apple_count'),
            deferred=True
        )
        query = (
            self.session.query(sa.inspect(self.Article))
            .outerjoin(self.Article.apples)
            .options(
                sa.orm.undefer(self.Article.apple_count)
            )
            .options(sa.orm.contains_eager(self.Article.apples))
        )
        query = sort_query(query, 'apple_count')
        assert 'ORDER BY apple_count' in str(query)

    def test_table(self):
        query = self.session.query(self.Article.__table__)
        query = sort_query(query, 'name')
        assert_contains('ORDER BY article.name', query)


class TestSortQueryRelationshipCounts(TestCase):
    """
    Currently this doesn't work with SQLite
    """
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def test_relation_hybrid_property(self):
        query = (
            self.session.query(self.Article)
            .join(self.Article.category)
        ).group_by(self.Article.id)
        query = sort_query(query, '-category-articles_count')
        assert_contains('ORDER BY (SELECT count(article.id) AS count_1', query)

    def test_aliased_hybrid_property(self):
        alias = sa.orm.aliased(
            self.Category,
            name='categories'
        )
        query = (
            self.session.query(self.Article)
            .outerjoin(alias, self.Article.category)
            .options(
                sa.orm.contains_eager(self.Article.category, alias=alias)
            )
        ).group_by(alias.id, self.Article.id)
        query = sort_query(query, '-categories-articles_count')
        assert_contains('ORDER BY (SELECT count(article.id) AS count_1', query)

    def test_aliased_concat_hybrid_property(self):
        alias = sa.orm.aliased(
            self.Category,
            name='aliased'
        )
        query = (
            self.session.query(self.Article)
            .outerjoin(alias, self.Article.category)
            .options(
                sa.orm.contains_eager(self.Article.category, alias=alias)
            )
        )
        query = sort_query(query, 'aliased-full_name')
        assert_contains(
            'concat(aliased.title, :param_1, aliased.name)', query
        )


class TestSortQueryWithPolymorphicInheritance(TestCase):
    """
    Currently this doesn't work with SQLite
    """
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class TextItem(self.Base):
            __tablename__ = 'text_item'
            id = sa.Column(sa.Integer, primary_key=True)

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
            category = sa.Column(sa.Unicode(255))
            __mapper_args__ = {
                'polymorphic_identity': u'article'
            }

        self.TextItem = TextItem
        self.Article = Article

    def test_column_property(self):
        self.TextItem.item_count = sa.orm.column_property(
            sa.select(
                [
                    sa.func.count('1')
                ],
            )
            .select_from(self.TextItem.__table__)
            .label('item_count')
        )

        query = sort_query(
            self.session.query(self.TextItem),
            'item_count'
        )
        assert_contains('ORDER BY item_count', query)

    def test_child_class_attribute(self):
        query = sort_query(
            self.session.query(self.TextItem),
            'category'
        )
        assert_contains('ORDER BY article.category ASC', query)

    def test_with_ambiguous_column(self):
        query = sort_query(
            self.session.query(self.TextItem),
            'id'
        )
        assert_contains('ORDER BY text_item.id ASC', query)


class TestSortQueryWithCustomPolymorphic(TestCase):
    """
    Currently this doesn't work with SQLite
    """
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class TextItem(self.Base):
            __tablename__ = 'text_item'
            id = sa.Column(sa.Integer, primary_key=True)

            type = sa.Column(sa.Unicode(255))

            __mapper_args__ = {
                'polymorphic_on': type,
            }

        class Article(TextItem):
            __tablename__ = 'article'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
            )
            category = sa.Column(sa.Unicode(255))
            __mapper_args__ = {
                'polymorphic_identity': u'article'
            }

        class BlogPost(TextItem):
            __tablename__ = 'blog_post'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
            )
            __mapper_args__ = {
                'polymorphic_identity': u'blog_post'
            }

        self.TextItem = TextItem
        self.Article = Article
        self.BlogPost = BlogPost

    def test_with_unknown_column(self):
        query = sort_query(
            self.session.query(
                sa.orm.with_polymorphic(self.TextItem, [self.BlogPost])
            ),
            'category'
        )
        assert 'ORDER BY' not in str(query)

    def test_with_existing_column(self):
        query = sort_query(
            self.session.query(
                sa.orm.with_polymorphic(self.TextItem, [self.Article])
            ),
            'category'
        )
        assert 'ORDER BY' in str(query)
