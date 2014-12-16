import sqlalchemy as sa
from sqlalchemy_utils.aggregates import select_aggregate
from tests import TestCase
from tests.mixins import (
    ThreeLevelDeepManyToMany,
    ThreeLevelDeepOneToMany,
    ThreeLevelDeepOneToOne,
)


def normalize(sql):
    return ' '.join(sql.replace('\n', '').split())


class TestAggregateQueryForDeepToManyToMany(
    ThreeLevelDeepManyToMany,
    TestCase
):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'
    create_tables = False

    def assert_sql(self, construct, sql):
        assert normalize(str(construct)) == normalize(sql)

    def build_update(self, *relationships):
        expr = sa.func.count(sa.text('1'))
        return (
            self.Catalog.__table__.update().values(
                _id=select_aggregate(
                    expr,
                    relationships
                ).correlate(self.Catalog)
            )
        )

    def test_simple_join(self):
        self.assert_sql(
            self.build_update(self.Catalog.categories),
            (
                '''UPDATE catalog SET _id=(SELECT count(1) AS count_1
                FROM category JOIN catalog_category ON category._id =
                catalog_category.category_id WHERE catalog._id =
                catalog_category.catalog_id)'''
            )
        )

    def test_two_relations(self):
        self.assert_sql(
            self.build_update(
                self.Category.sub_categories,
                self.Catalog.categories,
            ),
            (
                '''UPDATE catalog SET _id=(SELECT count(1) AS count_1
                FROM sub_category
                JOIN category_subcategory
                    ON sub_category._id = category_subcategory.subcategory_id
                JOIN category
                    ON category._id = category_subcategory.category_id
                JOIN catalog_category
                    ON category._id = catalog_category.category_id
                WHERE catalog._id = catalog_category.catalog_id)'''
            )
        )
