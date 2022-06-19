import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from sqlalchemy_utils import aggregated


@pytest.fixture
def Category(Base):
    class Category(Base):
        __tablename__ = 'category'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
    return Category


@pytest.fixture
def Catalog(Base, Category):
    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated(
            'products.categories',
            sa.Column(sa.Integer, default=0)
        )
        def category_count(self):
            return sa.func.count(sa.distinct(Category.id))
    return Catalog


@pytest.fixture
def Product(Base, Catalog, Category):
    product_categories = sa.Table(
        'category_product',
        Base.metadata,
        sa.Column('category_id', sa.Integer, sa.ForeignKey('category.id')),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('product.id'))
    )

    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        price = sa.Column(sa.Numeric)

        catalog_id = sa.Column(
            sa.Integer, sa.ForeignKey('catalog.id')
        )

        catalog = sa.orm.relationship(
            Catalog,
            backref='products'
        )

        categories = sa.orm.relationship(
            Category,
            backref='products',
            secondary=product_categories
        )
    return Product


@pytest.fixture
def init_models(Category, Catalog, Product):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestAggregateOneToManyAndManyToMany:

    def test_insert(self, session, Category, Catalog, Product):
        category = Category()
        session.add(category)
        products = [
            Product(categories=[category]),
            Product(categories=[category])
        ]
        [session.add(product) for product in products]
        catalog = Catalog(products=products)
        session.add(catalog)
        products2 = [
            Product(categories=[category]),
            Product(categories=[category])
        ]
        [session.add(product) for product in products2]
        catalog2 = Catalog(products=products2)
        session.add(catalog2)
        session.commit()
        assert catalog.category_count == 1
        assert catalog2.category_count == 1
