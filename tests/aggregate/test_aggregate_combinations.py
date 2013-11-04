from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy_utils.aggregates import aggregate
from tests import TestCase


class TestDeepModelPathsForAggregates(TestCase):
    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregate(sa.func.count, 'categories.products')
            def product_count(self):
                return sa.Column(sa.Integer, default=0)

            categories = sa.orm.relationship('Product', backref='catalog')

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)

            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

        self.Catalog = Catalog
        self.Product = Product

    def test_assigns_aggregates(self):
        catalog = self.Catalog(
            name=u'Some catalog'
        )
        self.session.add(catalog)
        self.session.commit()
        product = self.Product(
            name=u'Some product',
            price=Decimal('1000'),
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(catalog)
        assert catalog.product_count == 1
