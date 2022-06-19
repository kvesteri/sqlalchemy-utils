import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from sqlalchemy_utils import aggregated


@pytest.fixture
def Catalog(Base):
    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)

        @aggregated(
            'categories.sub_categories.products',
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
        catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

        sub_categories = sa.orm.relationship(
            'SubCategory', backref='category'
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
def catalog_factory(Product, SubCategory, Category, Catalog, session):
    def catalog_factory():
        product = Product()
        session.add(product)
        sub_category = SubCategory(products=[product])
        session.add(sub_category)
        category = Category(sub_categories=[sub_category])
        session.add(category)
        catalog = Catalog(categories=[category])
        session.add(catalog)
        return catalog
    return catalog_factory


@pytest.mark.usefixtures('postgresql_dsn')
class Test3LevelDeepOneToMany:

    def test_assigns_aggregates(self, session, catalog_factory):
        catalog = catalog_factory()
        session.commit()
        session.refresh(catalog)
        assert catalog.product_count == 1

    def catalog_factory(
        self,
        session,
        Product,
        SubCategory,
        Category,
        Catalog
    ):
        product = Product()
        session.add(product)
        sub_category = SubCategory(
            products=[product]
        )
        session.add(sub_category)
        category = Category(sub_categories=[sub_category])
        session.add(category)
        catalog = Catalog(categories=[category])
        session.add(catalog)
        return catalog

    def test_only_updates_affected_aggregates(
        self,
        session,
        catalog_factory,
        Product
    ):
        catalog = catalog_factory()
        catalog2 = catalog_factory()
        session.commit()

        # force set catalog2 product_count to zero in order to check if it gets
        # updated when the other catalog's product count gets updated
        session.execute(
            sa.text(
                'UPDATE catalog SET product_count = 0 WHERE id = %d' % catalog2.id
            )
        )

        catalog.categories[0].sub_categories[0].products.append(
            Product()
        )
        session.commit()
        session.refresh(catalog)
        session.refresh(catalog2)
        assert catalog.product_count == 2
        assert catalog2.product_count == 0
