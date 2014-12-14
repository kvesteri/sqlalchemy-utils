import sqlalchemy as sa

from sqlalchemy_utils.relationships import chained_join
from tests import TestCase


class TestChainedJoinForManyToManyToManyToMany(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'
    create_tables = False

    def create_models(self):
        catalog_category = sa.Table(
            'catalog_category',
            self.Base.metadata,
            sa.Column('catalog_id', sa.Integer, sa.ForeignKey('catalog.id')),
            sa.Column('category_id', sa.Integer, sa.ForeignKey('category.id'))
        )

        category_subcategory = sa.Table(
            'category_subcategory',
            self.Base.metadata,
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

        subcategory_product = sa.Table(
            'subcategory_product',
            self.Base.metadata,
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

        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)

            categories = sa.orm.relationship(
                'Category',
                backref='catalogs',
                secondary=catalog_category
            )

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)

            sub_categories = sa.orm.relationship(
                'SubCategory',
                backref='categories',
                secondary=category_subcategory
            )

        class SubCategory(self.Base):
            __tablename__ = 'sub_category'
            id = sa.Column(sa.Integer, primary_key=True)
            products = sa.orm.relationship(
                'Product',
                backref='sub_categories',
                secondary=subcategory_product
            )

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            price = sa.Column(sa.Numeric)

        self.Catalog = Catalog
        self.Category = Category
        self.SubCategory = SubCategory
        self.Product = Product

    def test_simple_join(self):
        assert str(chained_join(self.Catalog.categories)) == (
            'catalog_category JOIN category ON '
            'category.id = catalog_category.category_id'
        )

    def test_two_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories
        )
        assert str(sql) == (
            'catalog_category JOIN category ON category.id = '
            'catalog_category.category_id JOIN category_subcategory ON '
            'category.id = category_subcategory.category_id JOIN sub_category '
            'ON sub_category.id = category_subcategory.subcategory_id'
        )

    def test_three_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories,
            self.SubCategory.products
        )
        assert str(sql) == (
            'catalog_category JOIN category ON category.id = '
            'catalog_category.category_id JOIN category_subcategory ON '
            'category.id = category_subcategory.category_id JOIN sub_category '
            'ON sub_category.id = category_subcategory.subcategory_id JOIN '
            'subcategory_product ON sub_category.id = '
            'subcategory_product.subcategory_id JOIN product ON product.id = '
            'subcategory_product.product_id'
        )


class TestChainedJoinFor3LevelDeepOneToMany(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'
    create_tables = False

    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)

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

    def test_simple_join(self):
        assert str(chained_join(self.Catalog.categories)) == 'category'

    def test_two_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories
        )
        assert str(sql) == (
            'category JOIN sub_category ON category.id = '
            'sub_category.category_id'
        )

    def test_three_relations(self):
        sql = chained_join(
            self.Catalog.categories,
            self.Category.sub_categories,
            self.SubCategory.products
        )
        assert str(sql) == (
            'category JOIN sub_category ON category.id = '
            'sub_category.category_id JOIN product ON sub_category.id = '
            'product.sub_category_id'
        )


class TestChainedJoinForOneToOneToOneToOne(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
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

    def test_simple_join(self):
        assert str(chained_join(self.Catalog.category)) == 'category'

    def test_two_relations(self):
        sql = chained_join(
            self.Catalog.category,
            self.Category.sub_category
        )
        assert str(sql) == (
            'category JOIN sub_category ON category.id = '
            'sub_category.category_id'
        )

    def test_three_relations(self):
        sql = chained_join(
            self.Catalog.category,
            self.Category.sub_category,
            self.SubCategory.product
        )
        assert str(sql) == (
            'category JOIN sub_category ON category.id = '
            'sub_category.category_id JOIN product ON sub_category.id = '
            'product.sub_category_id'
        )
