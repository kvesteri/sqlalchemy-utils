import sqlalchemy as sa
from sqlalchemy_utils import aggregated, TSVectorType
from tests import TestCase


def tsvector_reduce_concat(vectors):
    return sa.sql.expression.cast(
        sa.func.coalesce(
            sa.func.array_to_string(sa.func.array_agg(vectors), ' ')
        ),
        TSVectorType
    )


class TestSearchVectorAggregates(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Catalog(self.Base):
            __tablename__ = 'catalog'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregated('products', sa.Column(TSVectorType))
            def product_search_vector(self):
                return tsvector_reduce_concat(
                    sa.func.to_tsvector(Product.name)
                )

            products = sa.orm.relationship('Product', backref='catalog')

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)

            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

        self.Catalog = Catalog
        self.Product = Product

    def test_assigns_aggregates_on_insert(self):
        catalog = self.Catalog(
            name=u'Some catalog'
        )
        self.session.add(catalog)
        self.session.commit()
        product = self.Product(
            name=u'Product XYZ',
            catalog=catalog
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(catalog)
        assert catalog.product_search_vector == "'product':1 'xyz':2"
