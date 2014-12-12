import sqlalchemy as sa

from tests import TestCase
from sqlalchemy_utils.observer import observes


class TestObservesFor3LevelDeepOneToMany(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
            product_count = sa.Column(sa.Integer, default=0)

            @observes('categories.sub_categories.products')
            def product_observer(self, products):
                self.product_count = len(products)

            categories = sa.orm.relationship('Category', backref='catalog')

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

            sub_categories = sa.orm.relationship(
                'SubCategory', backref='category'
            )

        class SubCategory(self.Base):
            __tablename__ = 'sub_category'
            id = sa.Column(sa.Integer, primary_key=True)
            category_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))
            products = sa.orm.relationship(
                'Product',
                backref='sub_category'
            )

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            price = sa.Column(sa.Numeric)

            sub_category_id = sa.Column(
                sa.Integer, sa.ForeignKey('sub_category.id')
            )

            def __repr__(self):
                return '<Product id=%r>' % self.id

        self.Catalog = Catalog
        self.Category = Category
        self.SubCategory = SubCategory
        self.Product = Product

    def create_catalog(self):
        sub_category = self.SubCategory(products=[self.Product()])
        category = self.Category(sub_categories=[sub_category])
        catalog = self.Catalog(categories=[category])
        self.session.add(catalog)
        self.session.commit()
        return catalog

    def test_simple_insert(self):
        catalog = self.create_catalog()
        assert catalog.product_count == 1

    def test_add_leaf_object(self):
        catalog = self.create_catalog()
        product = self.Product()
        catalog.categories[0].sub_categories[0].products.append(product)
        self.session.flush()
        assert catalog.product_count == 2

    def test_remove_leaf_object(self):
        catalog = self.create_catalog()
        product = self.Product()
        catalog.categories[0].sub_categories[0].products.append(product)
        self.session.flush()
        self.session.delete(product)
        self.session.commit()
        assert catalog.product_count == 1
        self.session.delete(
            catalog.categories[0].sub_categories[0].products[0]
        )
        self.session.commit()
        assert catalog.product_count == 0

    def test_delete_intermediate_object(self):
        catalog = self.create_catalog()
        self.session.delete(catalog.categories[0].sub_categories[0])
        self.session.commit()
        assert catalog.product_count == 0

    def test_gathered_objects_are_distinct(self):
        catalog = self.Catalog()
        category = self.Category(catalog=catalog)
        product = self.Product()
        category.sub_categories.append(
            self.SubCategory(products=[product])
        )
        self.session.add(
            self.SubCategory(category=category, products=[product])
        )
        self.session.commit()
        assert catalog.product_count == 1
