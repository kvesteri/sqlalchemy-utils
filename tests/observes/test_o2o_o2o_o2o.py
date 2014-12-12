import sqlalchemy as sa
from sqlalchemy_utils.observer import observes
from tests import TestCase


class TestObservesForOneToOneToOneToOne(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Catalog(self.Base):
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

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

            sub_category = sa.orm.relationship(
                'SubCategory',
                uselist=False,
                backref='category'
            )

        class SubCategory(self.Base):
            __tablename__ = 'sub_category'
            id = sa.Column(sa.Integer, primary_key=True)
            category_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))
            product = sa.orm.relationship(
                'Product',
                uselist=False,
                backref='sub_category'
            )

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            price = sa.Column(sa.Integer)

            sub_category_id = sa.Column(
                sa.Integer, sa.ForeignKey('sub_category.id')
            )

        self.Catalog = Catalog
        self.Category = Category
        self.SubCategory = SubCategory
        self.Product = Product

    def create_catalog(self):
        sub_category = self.SubCategory(product=self.Product(price=123))
        category = self.Category(sub_category=sub_category)
        catalog = self.Catalog(category=category)
        self.session.add(catalog)
        self.session.flush()
        return catalog

    def test_simple_insert(self):
        catalog = self.create_catalog()
        assert catalog.product_price == 123

    def test_replace_leaf_object(self):
        catalog = self.create_catalog()
        product = self.Product(price=44)
        catalog.category.sub_category.product = product
        self.session.flush()
        assert catalog.product_price == 44

    def test_delete_leaf_object(self):
        catalog = self.create_catalog()
        self.session.delete(catalog.category.sub_category.product)
        self.session.flush()
        assert catalog.product_price is None
