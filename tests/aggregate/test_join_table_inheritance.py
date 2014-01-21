from decimal import Decimal
import sqlalchemy as sa
from sqlalchemy_utils.aggregates import aggregated
from tests import TestCase


class TestLazyEvaluatedSelectExpressionsForAggregates(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Catalog(self.Base):
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

        class CostumeCatalog(Catalog):
            __tablename__ = 'costume_catalog'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(Catalog.id), primary_key=True
            )

            __mapper_args__ = {
                'polymorphic_identity': 'costumes',
            }

        class CarCatalog(Catalog):
            __tablename__ = 'car_catalog'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(Catalog.id), primary_key=True
            )

            __mapper_args__ = {
                'polymorphic_identity': 'cars',
            }

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            price = sa.Column(sa.Numeric)

            catalog_id = sa.Column(sa.Integer, sa.ForeignKey('catalog.id'))

        self.Catalog = Catalog
        self.CostumeCatalog = CostumeCatalog
        self.CarCatalog = CarCatalog
        self.Product = Product

    def test_columns_inherited_from_parent(self):
        assert self.CarCatalog.net_worth
        assert self.CostumeCatalog.net_worth
        assert self.Catalog.net_worth
        assert not hasattr(self.CarCatalog.__table__.c, 'net_worth')
        assert not hasattr(self.CostumeCatalog.__table__.c, 'net_worth')

    def test_assigns_aggregates_on_insert(self):
        catalog = self.Catalog(
            name=u'Some catalog'
        )
        self.session.add(catalog)
        self.session.commit()
        product = self.Product(
            name=u'Some product',
            price=Decimal('1000'),
            catalog=catalog
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(catalog)
        assert catalog.net_worth == Decimal('1000')

    def test_assigns_aggregates_on_update(self):
        catalog = self.Catalog(
            name=u'Some catalog'
        )
        self.session.add(catalog)
        self.session.commit()
        product = self.Product(
            name=u'Some product',
            price=Decimal('1000'),
            catalog=catalog
        )
        self.session.add(product)
        self.session.commit()
        product.price = Decimal('500')
        self.session.commit()
        self.session.refresh(catalog)
        assert catalog.net_worth == Decimal('500')
