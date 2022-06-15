from decimal import Decimal

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.aggregates import aggregated


@pytest.fixture
def Product(Base):
    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        price = sa.Column(sa.Numeric)

        catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))
    return Product


@pytest.fixture
def Catalog(Base, Product):
    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated('products', sa.Column(sa.Numeric, default=0))
        def net_worth(self):
            return sa.func.sum(Product.price)

        products = sa.orm.relationship('Product', backref='catalog')
    return Catalog


@pytest.fixture
def init_models(Product, Catalog):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestLazyEvaluatedSelectExpressionsForAggregates:

    def test_assigns_aggregates_on_insert(self, session, Product, Catalog):
        catalog = Catalog(
            name='Some catalog'
        )
        session.add(catalog)
        session.commit()
        product = Product(
            name='Some product',
            price=Decimal('1000'),
            catalog=catalog
        )
        session.add(product)
        session.commit()
        session.refresh(catalog)
        assert catalog.net_worth == Decimal('1000')

    def test_assigns_aggregates_on_update(self, session, Product, Catalog):
        catalog = Catalog(
            name='Some catalog'
        )
        session.add(catalog)
        session.commit()
        product = Product(
            name='Some product',
            price=Decimal('1000'),
            catalog=catalog
        )
        session.add(product)
        session.commit()
        product.price = Decimal('500')
        session.commit()
        session.refresh(catalog)
        assert catalog.net_worth == Decimal('500')
