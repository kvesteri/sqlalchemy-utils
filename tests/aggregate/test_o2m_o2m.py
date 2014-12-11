from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy_utils.aggregates import aggregated
from tests import TestCase


class TestAggregateOneToManyAndOneToMany(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregated(
                'categories.products',
                sa.Column(sa.Integer, default=0)
            )
            def product_count(self):
                return sa.func.count('1')

            categories = sa.orm.relationship('Category', backref='catalog')

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

            products = sa.orm.relationship('Product', backref='category')

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)

            category_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))

        self.Catalog = Catalog
        self.Category = Category
        self.Product = Product

    def test_assigns_aggregates(self):
        category = self.Category(name=u'Some category')
        catalog = self.Catalog(
            categories=[category]
        )
        catalog.name = u'Some catalog'
        self.session.add(catalog)
        self.session.commit()
        product = self.Product(
            name=u'Some product',
            price=Decimal('1000'),
            category=category
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(catalog)
        assert catalog.product_count == 1
