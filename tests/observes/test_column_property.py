import sqlalchemy as sa

from sqlalchemy_utils.observer import observes
from tests import TestCase


class TestObservesForColumn(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            price = sa.Column(sa.Integer)

            @observes('price')
            def product_price_observer(self, price):
                self.price = price * 2

        self.Product = Product

    def test_simple_insert(self):
        product = self.Product(price=100)
        self.session.add(product)
        self.session.flush()
        assert product.price == 200
