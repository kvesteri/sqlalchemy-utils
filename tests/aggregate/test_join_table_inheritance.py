from decimal import Decimal

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.aggregates import aggregated


@pytest.fixture
def Product(Base):
    class Product(Base):
        __tablename__ = 'product'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        price = sa.Column(sa.Numeric)
        type = sa.Column(sa.String(255))

        __mapper_args__ = {
            'polymorphic_on': type,
            'polymorphic_identity': 'simple'
        }

        catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))
    return Product


@pytest.fixture(params=['simple', 'child'])
def AnyProduct(Product, request):
    if request.param == 'simple':
        return Product

    class ChildProduct(Product):
        __tablename__ = 'child_product'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(Product.id), primary_key=True
        )

        __mapper_args__ = {
            'polymorphic_identity': 'child',
        }
    return ChildProduct


@pytest.fixture
def Catalog(Base, Product):
    class Catalog(Base):
        __tablename__ = 'catalog'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        type = sa.Column(sa.Unicode(255))

        __mapper_args__ = {
            'polymorphic_on': type
        }

        @aggregated('products', sa.Column(sa.Numeric, default=0))
        def net_worth(self):
            return sa.func.sum(Product.price)

        products = sa.orm.relationship('Product', backref='catalog')
    return Catalog


@pytest.fixture
def CostumeCatalog(Catalog):
    class CostumeCatalog(Catalog):
        __tablename__ = 'costume_catalog'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(Catalog.id), primary_key=True
        )

        __mapper_args__ = {
            'polymorphic_identity': 'costumes',
        }
    return CostumeCatalog


@pytest.fixture
def CarCatalog(Catalog):
    class CarCatalog(Catalog):
        __tablename__ = 'car_catalog'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(Catalog.id), primary_key=True
        )

        __mapper_args__ = {
            'polymorphic_identity': 'cars',
        }
    return CarCatalog


@pytest.fixture
def init_models(AnyProduct, Catalog, CostumeCatalog, CarCatalog):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestLazyEvaluatedSelectExpressionsForAggregates:

    def test_columns_inherited_from_parent(
        self,
        Catalog,
        CarCatalog,
        CostumeCatalog
    ):
        assert CarCatalog.net_worth
        assert CostumeCatalog.net_worth
        assert Catalog.net_worth
        assert not hasattr(CarCatalog.__table__.c, 'net_worth')
        assert not hasattr(CostumeCatalog.__table__.c, 'net_worth')

    def test_assigns_aggregates_on_insert(self, session, AnyProduct, Catalog):
        catalog = Catalog(
            name='Some catalog'
        )
        session.add(catalog)
        session.commit()
        product = AnyProduct(
            name='Some product',
            price=Decimal('1000'),
            catalog=catalog
        )
        session.add(product)
        session.commit()
        session.refresh(catalog)
        assert catalog.net_worth == Decimal('1000')

    def test_assigns_aggregates_on_update(self, session, Catalog, AnyProduct):
        catalog = Catalog(
            name='Some catalog'
        )
        session.add(catalog)
        session.commit()
        product = AnyProduct(
            name='Some product',
            price=Decimal('1000'),
            catalog=catalog
        )
        session.add(product)
        session.commit()
        product.price = Decimal('500')
        session.commit()
        session.refresh(catalog)
        assert catalog.net_worth == Decimal('500')
