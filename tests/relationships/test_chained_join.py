from sqlalchemy_utils.relationships import chained_join
from tests import TestCase
from tests.mixins import (
    ThreeLevelDeepManyToMany,
    ThreeLevelDeepOneToMany,
    ThreeLevelDeepOneToOne,
)


class TestChainedJoinFoDeepToManyToMany(ThreeLevelDeepManyToMany, TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'
    create_tables = False

    def test_simple_join(self):
        assert str(chained_join(self.Catalog.categories)) == (
            'catalog_category JOIN category ON '
            'category._id = catalog_category.category_id'
        )

    def test_two_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories
        )
        assert str(sql) == (
            'catalog_category JOIN category ON category._id = '
            'catalog_category.category_id JOIN category_subcategory ON '
            'category._id = category_subcategory.category_id JOIN '
            'sub_category ON sub_category._id = '
            'category_subcategory.subcategory_id'
        )

    def test_three_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories,
            self.SubCategory.products
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


class TestChainedJoinForDeepOneToMany(ThreeLevelDeepOneToMany, TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'
    create_tables = False

    def test_simple_join(self):
        assert str(chained_join(self.Catalog.categories)) == 'category'

    def test_two_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id'
        )

    def test_three_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories,
            self.SubCategory.products
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id JOIN product ON sub_category._id = '
            'product._sub_category_id'
        )


class TestChainedJoinForDeepOneToOne(ThreeLevelDeepOneToOne, TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'
    create_tables = False

    def test_simple_join(self):
        assert str(chained_join(self.Catalog.category)) == 'category'

    def test_two_relations(self):
        sql = chained_join(
            self.Catalog.category,
            self.Category.sub_category
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id'
        )

    def test_three_relations(self):
        sql = chained_join(
            self.Catalog.category,
            self.Category.sub_category,
            self.SubCategory.product
        )
        assert str(sql) == (
            'category JOIN sub_category ON category._id = '
            'sub_category._category_id JOIN product ON sub_category._id = '
            'product._sub_category_id'
        )
