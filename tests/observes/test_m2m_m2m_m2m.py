import pytest
import sqlalchemy as sa

from sqlalchemy_utils.observer import observes


@pytest.fixture
def Catalog(Base):
    catalog_category = sa.Table(
        'catalog_category',
        Base.metadata,
        sa.Column('catalog_id', sa.Integer, sa.ForeignKey('catalog.id')),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('category.id'))
    )

    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        product_count = sa.Column(sa.Integer, default=0)

        @observes('categories.sub_categories.products')
        def product_observer(self, products):
            self.product_count = len(products)

        categories = sa.orm.relationship(
            'Category',
            backref='catalogs',
            secondary=catalog_category
        )
    return Catalog


@pytest.fixture
def Category(Base):
    category_subcategory = sa.Table(
        'category_subcategory',
        Base.metadata,
        sa.Column(
            'category_id',
            sa.Integer,
            sa.ForeignKey('category.id')
        ),
        sa.Column(
            'subcategory_id',
            sa.Integer,
            sa.ForeignKey('sub_category.id')
        )
    )

    class Category(Base):
        __tablename__ = 'category'
        id = sa.Column(sa.Integer, primary_key=True)

        sub_categories = sa.orm.relationship(
            'SubCategory',
            backref='categories',
            secondary=category_subcategory
        )
    return Category


@pytest.fixture
def SubCategory(Base):
    subcategory_product = sa.Table(
        'subcategory_product',
        Base.metadata,
        sa.Column(
            'subcategory_id',
            sa.Integer,
            sa.ForeignKey('sub_category.id')
        ),
        sa.Column(
            'product_id',
            sa.Integer,
            sa.ForeignKey('product.id')
        )
    )

    class SubCategory(Base):
        __tablename__ = 'sub_category'
        id = sa.Column(sa.Integer, primary_key=True)
        products = sa.orm.relationship(
            'Product',
            backref='sub_categories',
            secondary=subcategory_product
        )

    return SubCategory


@pytest.fixture
def Product(Base):
    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        price = sa.Column(sa.Numeric)
    return Product


@pytest.fixture
def init_models(Catalog, Category, SubCategory, Product):
    pass


@pytest.fixture
def catalog(session, Catalog, Category, SubCategory, Product):
    sub_category = SubCategory(products=[Product()])
    category = Category(sub_categories=[sub_category])
    catalog = Catalog(categories=[category])
    session.add(catalog)
    session.flush()
    return catalog


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForManyToManyToManyToMany:

    def test_simple_insert(self, catalog):
        assert catalog.product_count == 1

    def test_add_leaf_object(self, catalog, session, Product):
        product = Product()
        catalog.categories[0].sub_categories[0].products.append(product)
        session.flush()
        assert catalog.product_count == 2

    def test_remove_leaf_object(self, catalog, session, Product):
        product = Product()
        catalog.categories[0].sub_categories[0].products.append(product)
        session.flush()
        session.delete(product)
        session.flush()
        assert catalog.product_count == 1

    def test_delete_intermediate_object(self, catalog, session):
        session.delete(catalog.categories[0].sub_categories[0])
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
        category = Category(catalogs=[catalog])
        product = Product()
        category.sub_categories.append(
            SubCategory(products=[product])
        )
        session.add(
            SubCategory(categories=[category], products=[product])
        )
        session.commit()
        assert catalog.product_count == 1
