import pytest
import sqlalchemy as sa

from sqlalchemy_utils.observer import observes


@pytest.fixture
def Catalog(Base):
    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        product_price = sa.Column(sa.Integer)

        @observes('category.sub_category.product')
        def product_observer(self, product):
            self.product_price = product.price if product else None

        category = sa.orm.relationship(
            'Category',
            uselist=False,
            backref='catalog'
        )
    return Catalog


@pytest.fixture
def Category(Base):
    class Category(Base):
        __tablename__ = 'category'
        id = sa.Column(sa.Integer, primary_key=True)
        catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

        sub_category = sa.orm.relationship(
            'SubCategory',
            uselist=False,
            backref='category'
        )
    return Category


@pytest.fixture
def SubCategory(Base):
    class SubCategory(Base):
        __tablename__ = 'sub_category'
        id = sa.Column(sa.Integer, primary_key=True)
        category_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))
        product = sa.orm.relationship(
            'Product',
            uselist=False,
            backref='sub_category'
        )
    return SubCategory


@pytest.fixture
def Product(Base):
    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        price = sa.Column(sa.Integer)

        sub_category_id = sa.Column(
            sa.Integer, sa.ForeignKey('sub_category.id')
        )
    return Product


@pytest.fixture
def init_models(Catalog, Category, SubCategory, Product):
    pass


@pytest.fixture
def catalog(session, Catalog, Category, SubCategory, Product):
    sub_category = SubCategory(product=Product(price=123))
    category = Category(sub_category=sub_category)
    catalog = Catalog(category=category)
    session.add(catalog)
    session.flush()
    return catalog


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForOneToOneToOneToOne:

    def test_simple_insert(self, catalog):
        assert catalog.product_price == 123

    def test_replace_leaf_object(self, catalog, session, Product):
        product = Product(price=44)
        catalog.category.sub_category.product = product
        session.flush()
        assert catalog.product_price == 44

    def test_delete_leaf_object(self, catalog, session):
        session.delete(catalog.category.sub_category.product)
        session.flush()
        assert catalog.product_price is None
