import pytest
import sqlalchemy as sa


class ThreeLevelDeepOneToOne:

    @pytest.fixture
    def Catalog(self, Base, Category):
        class Catalog(Base):
            __tablename__ = 'catalog'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            category = sa.orm.relationship(
                Category,
                uselist=False,
                backref='catalog'
            )
        return Catalog

    @pytest.fixture
    def Category(self, Base, SubCategory):
        class Category(Base):
            __tablename__ = 'category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            catalog_id = sa.Column(
                '_catalog_id',
                sa.Integer,
                sa.ForeignKey('catalog._id')
            )

            sub_category = sa.orm.relationship(
                SubCategory,
                uselist=False,
                backref='category'
            )
        return Category

    @pytest.fixture
    def SubCategory(self, Base, Product):
        class SubCategory(Base):
            __tablename__ = 'sub_category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            category_id = sa.Column(
                '_category_id',
                sa.Integer,
                sa.ForeignKey('category._id')
            )
            product = sa.orm.relationship(
                Product,
                uselist=False,
                backref='sub_category'
            )
        return SubCategory

    @pytest.fixture
    def Product(self, Base):
        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            price = sa.Column(sa.Integer)

            sub_category_id = sa.Column(
                '_sub_category_id',
                sa.Integer,
                sa.ForeignKey('sub_category._id')
            )
        return Product

    @pytest.fixture
    def init_models(self, Catalog, Category, SubCategory, Product):
        pass


class ThreeLevelDeepOneToMany:

    @pytest.fixture
    def Catalog(self, Base, Category):
        class Catalog(Base):
            __tablename__ = 'catalog'
            id = sa.Column('_id', sa.Integer, primary_key=True)

            categories = sa.orm.relationship(Category, backref='catalog')
        return Catalog

    @pytest.fixture
    def Category(self, Base, SubCategory):
        class Category(Base):
            __tablename__ = 'category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            catalog_id = sa.Column(
                '_catalog_id',
                sa.Integer,
                sa.ForeignKey('catalog._id')
            )

            sub_categories = sa.orm.relationship(
                SubCategory, backref='category'
            )
        return Category

    @pytest.fixture
    def SubCategory(self, Base, Product):
        class SubCategory(Base):
            __tablename__ = 'sub_category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            category_id = sa.Column(
                '_category_id',
                sa.Integer,
                sa.ForeignKey('category._id')
            )
            products = sa.orm.relationship(
                Product,
                backref='sub_category'
            )
        return SubCategory

    @pytest.fixture
    def Product(self, Base):
        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            price = sa.Column(sa.Numeric)

            sub_category_id = sa.Column(
                '_sub_category_id',
                sa.Integer,
                sa.ForeignKey('sub_category._id')
            )

            def __repr__(self):
                return '<Product id=%r>' % self.id
        return Product

    @pytest.fixture
    def init_models(self, Catalog, Category, SubCategory, Product):
        pass


class ThreeLevelDeepManyToMany:

    @pytest.fixture
    def Catalog(self, Base, Category):

        catalog_category = sa.Table(
            'catalog_category',
            Base.metadata,
            sa.Column('catalog_id', sa.Integer, sa.ForeignKey('catalog._id')),
            sa.Column('category_id', sa.Integer, sa.ForeignKey('category._id'))
        )

        class Catalog(Base):
            __tablename__ = 'catalog'
            id = sa.Column('_id', sa.Integer, primary_key=True)

            categories = sa.orm.relationship(
                Category,
                backref='catalogs',
                secondary=catalog_category
            )
        return Catalog

    @pytest.fixture
    def Category(self, Base, SubCategory):

        category_subcategory = sa.Table(
            'category_subcategory',
            Base.metadata,
            sa.Column(
                'category_id',
                sa.Integer,
                sa.ForeignKey('category._id')
            ),
            sa.Column(
                'subcategory_id',
                sa.Integer,
                sa.ForeignKey('sub_category._id')
            )
        )

        class Category(Base):
            __tablename__ = 'category'
            id = sa.Column('_id', sa.Integer, primary_key=True)

            sub_categories = sa.orm.relationship(
                SubCategory,
                backref='categories',
                secondary=category_subcategory
            )
        return Category

    @pytest.fixture
    def SubCategory(self, Base, Product):

        subcategory_product = sa.Table(
            'subcategory_product',
            Base.metadata,
            sa.Column(
                'subcategory_id',
                sa.Integer,
                sa.ForeignKey('sub_category._id')
            ),
            sa.Column(
                'product_id',
                sa.Integer,
                sa.ForeignKey('product._id')
            )
        )

        class SubCategory(Base):
            __tablename__ = 'sub_category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            products = sa.orm.relationship(
                Product,
                backref='sub_categories',
                secondary=subcategory_product
            )
        return SubCategory

    @pytest.fixture
    def Product(self, Base):
        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            price = sa.Column(sa.Numeric)
        return Product

    @pytest.fixture
    def init_models(self, Catalog, Category, SubCategory, Product):
        pass
