from decimal import Decimal

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.aggregates import aggregated


@pytest.fixture
def Catalog(Base):
    class Catalog(Base):
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
    return Catalog


@pytest.fixture
def Category(Base):
    class Category(Base):
        __tablename__ = 'category'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

        products = sa.orm.relationship('Product', backref='category')
    return Category


@pytest.fixture
def Product(Base):
    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        price = sa.Column(sa.Numeric)

        category_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))
    return Product


@pytest.fixture
def init_models(Catalog, Category, Product):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestAggregateOneToManyAndOneToMany:

    def test_assigns_aggregates(self, session, Category, Catalog, Product):
        category = Category(name='Some category')
        catalog = Catalog(
            categories=[category]
        )
        catalog.name = 'Some catalog'
        session.add(catalog)
        session.commit()
        product = Product(
            name='Some product',
            price=Decimal('1000'),
            category=category
        )
        session.add(product)
        session.commit()
        session.refresh(catalog)
        assert catalog.product_count == 1
