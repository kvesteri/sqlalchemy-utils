import sqlalchemy as sa

from sqlalchemy_utils import aggregated
from tests import TestCase


class TestAggregateManyToManyAndManyToMany(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        catalog_products = sa.Table(
            'catalog_product',
            self.Base.metadata,
            sa.Column('catalog_id', sa.Integer, sa.ForeignKey('catalog.id')),
            sa.Column('product_id', sa.Integer, sa.ForeignKey('product.id'))
        )

        product_categories = sa.Table(
            'category_product',
            self.Base.metadata,
            sa.Column('category_id', sa.Integer, sa.ForeignKey('category.id')),
            sa.Column('product_id', sa.Integer, sa.ForeignKey('product.id'))
        )

        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregated(
                'products.categories',
                sa.Column(sa.Integer, default=0)
            )
            def category_count(self):
                return sa.func.count(sa.distinct(Category.id))

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)

            catalog_id = sa.Column(
                sa.Integer, sa.ForeignKey('catalog.id')
            )

            catalogs = sa.orm.relationship(
                Catalog,
                backref='products',
                secondary=catalog_products
            )

            categories = sa.orm.relationship(
                Category,
                backref='products',
                secondary=product_categories
            )

        self.Catalog = Catalog
        self.Category = Category
        self.Product = Product

    def test_insert(self):
        category = self.Category()
        products = [
            self.Product(categories=[category]),
            self.Product(categories=[category])
        ]
        catalog = self.Catalog(products=products)
        self.session.add(catalog)
        catalog2 = self.Catalog(products=products)
        self.session.add(catalog)
        self.session.commit()
        assert catalog.category_count == 1
        assert catalog2.category_count == 1
