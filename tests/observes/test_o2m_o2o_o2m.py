import pytest
import sqlalchemy as sa

from sqlalchemy_utils.observer import observes


@pytest.fixture
def Catalog(Base):
    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        product_count = sa.Column(sa.Integer, default=0)

        @observes('categories.sub_category.products')
        def product_observer(self, products):
            self.product_count = len(products)

        categories = sa.orm.relationship('Category', backref='catalog')
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
        products = sa.orm.relationship('Product', backref='sub_category')
    return SubCategory


@pytest.fixture
def Product(Base):
    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        price = sa.Column(sa.Numeric)

        sub_category_id = sa.Column(
            sa.Integer, sa.ForeignKey('sub_category.id')
        )
    return Product


@pytest.fixture
def init_models(Catalog, Category, SubCategory, Product):
    pass


@pytest.fixture
def catalog(session, Catalog, Category, SubCategory, Product):
    sub_category = SubCategory(products=[Product()])
    category = Category(sub_category=sub_category)
    catalog = Catalog(categories=[category])
    session.add(catalog)
    session.flush()
    return catalog


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForOneToManyToOneToMany:

    def test_simple_insert(self, catalog):
        assert catalog.product_count == 1

    def test_add_leaf_object(self, catalog, session, Product):
        product = Product()
        catalog.categories[0].sub_category.products.append(product)
        session.flush()
        assert catalog.product_count == 2

    def test_remove_leaf_object(self, catalog, session, Product):
        product = Product()
        catalog.categories[0].sub_category.products.append(product)
        session.flush()
        session.delete(product)
        session.flush()
        assert catalog.product_count == 1

    def test_delete_intermediate_object(self, catalog, session):
        session.delete(catalog.categories[0].sub_category)
        session.commit()
        assert catalog.product_count == 0

    def test_gathered_objects_are_distinct(
        self,
        session,
        Catalog,
        Category,
        SubCategory,
        Product
    ):
        catalog = Catalog()
        category = Category(catalog=catalog)
        product = Product()
        category.sub_category = SubCategory(products=[product])
        session.add(
            Category(catalog=catalog, sub_category=category.sub_category)
        )
        session.commit()
        assert catalog.product_count == 1
