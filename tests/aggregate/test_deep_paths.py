from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy_utils.aggregates import aggregated
from tests import TestCase


class TestDeepModelPathsForAggregates(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Catalog(self.Base):
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

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

            products = sa.orm.relationship('Product', backref='category')

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)

            category_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))

        self.Catalog = Catalog
        self.Category = Category
        self.Product = Product

    def test_assigns_aggregates(self):
        category = self.Category(name=u'Some category')
        catalog = self.Catalog(
            categories=[category]
        )
        catalog.name = u'Some catalog'
        self.session.add(catalog)
        self.session.commit()
        product = self.Product(
            name=u'Some product',
            price=Decimal('1000'),
            category=category
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(catalog)
        assert catalog.product_count == 1


class Test3LevelDeepModelPathsForAggregates(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'
    n = 1

    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregated(
                'categories.sub_categories.products',
                sa.Column(sa.Integer, default=0)
            )
            def product_count(self):
                return sa.func.count('1')

            categories = sa.orm.relationship('Category', backref='catalog')

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

            sub_categories = sa.orm.relationship(
                'SubCategory', backref='category'
            )

        class SubCategory(self.Base):
            __tablename__ = 'sub_category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            category_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))

            products = sa.orm.relationship('Product', backref='sub_category')

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)

            sub_category_id = sa.Column(
                sa.Integer, sa.ForeignKey('sub_category.id')
            )

        self.Catalog = Catalog
        self.Category = Category
        self.SubCategory = SubCategory
        self.Product = Product

    def test_assigns_aggregates(self):
        catalog = self.catalog_factory()
        self.session.commit()
        self.session.refresh(catalog)
        assert catalog.product_count == 1

    def catalog_factory(self):
        product = self.Product(
            name=u'Product %d' % self.n
        )
        sub_category = self.SubCategory(
            name=u'SubCategory %d' % self.n,
            products=[product]
        )
        category = self.Category(
            name=u'Category %d' % self.n,
            sub_categories=[sub_category]
        )
        catalog = self.Catalog(
            categories=[category]
        )
        catalog.name = u'Catalog %d' % self.n
        self.session.add(catalog)
        self.n += 1
        return catalog

    def test_only_updates_affected_aggregates(self):
        catalog = self.catalog_factory()
        catalog2 = self.catalog_factory()
        self.session.commit()

        # force set catalog2 product_count to zero in order to check if it gets
        # updated when the other catalog's product count gets updated
        self.session.execute(
            'UPDATE catalog SET product_count = 0 WHERE id = %d'
            % catalog2.id
        )

        catalog.categories[0].sub_categories[0].products.append(
            self.Product(name=u'Product 3')
        )
        self.session.commit()
        self.session.refresh(catalog)
        self.session.refresh(catalog2)
        assert catalog.product_count == 2
        assert catalog2.product_count == 0
