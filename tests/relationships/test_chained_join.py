import pytest

from sqlalchemy_utils.relationships import chained_join

from ..mixins import (
    ThreeLevelDeepManyToMany,
    ThreeLevelDeepOneToMany,
    ThreeLevelDeepOneToOne
)


@pytest.mark.usefixtures('postgresql_dsn')
class TestChainedJoinFoDeepToManyToMany(ThreeLevelDeepManyToMany):

    def test_simple_join(self, Catalog):
        assert str(chained_join(Catalog.categories)) == (
            'catalog_category JOIN category ON '
            'category._id = catalog_category.category_id'
        )

    def test_two_relations(self, Catalog, Category):
        sql = chained_join(
            Catalog.categories,
            Category.sub_categories
        )
        assert str(sql) == (
            'catalog_category JOIN category ON category._id = '
            'catalog_category.category_id JOIN category_subcategory ON '
            'category._id = category_subcategory.category_id JOIN '
            'sub_category ON sub_category._id = '
            'category_subcategory.subcategory_id'
        )

    def test_three_relations(self, Catalog, Category, SubCategory):
        sql = chained_join(
            Catalog.categories,
            Category.sub_categories,
            SubCategory.products
        )
        assert str(sql) == (
            'catalog_category JOIN category ON category._id = '
            'catalog_category.category_id JOIN category_subcategory ON '
            'category._id = category_subcategory.category_id JOIN sub_category'
            ' ON sub_category._id = category_subcategory.subcategory_id JOIN '
            'subcategory_product ON sub_category._id = '
            'subcategory_product.subcategory_id JOIN product ON product._id ='
            ' subcategory_product.product_id'
        )


@pytest.mark.usefixtures('postgresql_dsn')
class TestChainedJoinForDeepOneToMany(ThreeLevelDeepOneToMany):

    def test_simple_join(self, Catalog):
        assert str(chained_join(Catalog.categories)) == 'category'

    def test_two_relations(self, Catalog, Category):
        sql = chained_join(
            Catalog.categories,
            Category.sub_categories
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id'
        )

    def test_three_relations(self, Catalog, Category, SubCategory):
        sql = chained_join(
            Catalog.categories,
            Category.sub_categories,
            SubCategory.products
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id JOIN product ON sub_category._id = '
            'product._sub_category_id'
        )


@pytest.mark.usefixtures('postgresql_dsn')
class TestChainedJoinForDeepOneToOne(ThreeLevelDeepOneToOne):

    def test_simple_join(self, Catalog):
        assert str(chained_join(Catalog.category)) == 'category'

    def test_two_relations(self, Catalog, Category):
        sql = chained_join(
            Catalog.category,
            Category.sub_category
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id'
        )

    def test_three_relations(self, Catalog, Category, SubCategory):
        sql = chained_join(
            Catalog.category,
            Category.sub_category,
            SubCategory.product
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id JOIN product ON sub_category._id = '
            'product._sub_category_id'
        )
