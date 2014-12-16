import sqlalchemy as sa


class ThreeLevelDeepOneToOne(object):
    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            category = sa.orm.relationship(
                'Category',
                uselist=False,
                backref='catalog'
            )

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            catalog_id = sa.Column(
                '_catalog_id',
                sa.Integer,
                sa.ForeignKey('catalog._id')
            )

            sub_category = sa.orm.relationship(
                'SubCategory',
                uselist=False,
                backref='category'
            )

        class SubCategory(self.Base):
            __tablename__ = 'sub_category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            category_id = sa.Column(
                '_category_id',
                sa.Integer,
                sa.ForeignKey('category._id')
            )
            product = sa.orm.relationship(
                'Product',
                uselist=False,
                backref='sub_category'
            )

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            price = sa.Column(sa.Integer)

            sub_category_id = sa.Column(
                '_sub_category_id',
                sa.Integer,
                sa.ForeignKey('sub_category._id')
            )

        self.Catalog = Catalog
        self.Category = Category
        self.SubCategory = SubCategory
        self.Product = Product


class ThreeLevelDeepOneToMany(object):
    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column('_id', sa.Integer, primary_key=True)

            categories = sa.orm.relationship('Category', backref='catalog')

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            catalog_id = sa.Column(
                '_catalog_id',
                sa.Integer,
                sa.ForeignKey('catalog._id')
            )

            sub_categories = sa.orm.relationship(
                'SubCategory', backref='category'
            )

        class SubCategory(self.Base):
            __tablename__ = 'sub_category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            category_id = sa.Column(
                '_category_id',
                sa.Integer,
                sa.ForeignKey('category._id')
            )
            products = sa.orm.relationship(
                'Product',
                backref='sub_category'
            )

        class Product(self.Base):
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

        self.Catalog = Catalog
        self.Category = Category
        self.SubCategory = SubCategory
        self.Product = Product


class ThreeLevelDeepManyToMany(object):
    def create_models(self):
        catalog_category = sa.Table(
            'catalog_category',
            self.Base.metadata,
            sa.Column('catalog_id', sa.Integer, sa.ForeignKey('catalog._id')),
            sa.Column('category_id', sa.Integer, sa.ForeignKey('category._id'))
        )

        category_subcategory = sa.Table(
            'category_subcategory',
            self.Base.metadata,
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

        subcategory_product = sa.Table(
            'subcategory_product',
            self.Base.metadata,
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

        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column('_id', sa.Integer, primary_key=True)

            categories = sa.orm.relationship(
                'Category',
                backref='catalogs',
                secondary=catalog_category
            )

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column('_id', sa.Integer, primary_key=True)

            sub_categories = sa.orm.relationship(
                'SubCategory',
                backref='categories',
                secondary=category_subcategory
            )

        class SubCategory(self.Base):
            __tablename__ = 'sub_category'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            products = sa.orm.relationship(
                'Product',
                backref='sub_categories',
                secondary=subcategory_product
            )

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column('_id', sa.Integer, primary_key=True)
            price = sa.Column(sa.Numeric)

        self.Catalog = Catalog
        self.Category = Category
        self.SubCategory = SubCategory
        self.Product = Product
