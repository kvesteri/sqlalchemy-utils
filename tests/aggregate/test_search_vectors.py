import pytest
import sqlalchemy as sa

from sqlalchemy_utils import aggregated, TSVectorType


def tsvector_reduce_concat(vectors):
    return sa.sql.expression.cast(
        sa.func.coalesce(
            sa.func.array_to_string(sa.func.array_agg(vectors), ' ')
        ),
        TSVectorType
    )


@pytest.fixture
def Product(Base):
    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        price = sa.Column(sa.Numeric)

        catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))
    return Product


@pytest.fixture
def Catalog(Base, Product):
    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated('products', sa.Column(TSVectorType))
        def product_search_vector(self):
            return tsvector_reduce_concat(
                sa.func.to_tsvector(Product.name)
            )

        products = sa.orm.relationship('Product', backref='catalog')
    return Catalog


@pytest.fixture
def init_models(Product, Catalog):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestSearchVectorAggregates:

    def test_assigns_aggregates_on_insert(self, session, Product, Catalog):
        catalog = Catalog(
            name='Some catalog'
        )
        session.add(catalog)
        session.commit()
        product = Product(
            name='Product XYZ',
            catalog=catalog
        )
        session.add(product)
        session.commit()
        session.refresh(catalog)
        assert catalog.product_search_vector == "'product':1 'xyz':2"
