import sqlalchemy as sa
from flexmock import flexmock
from pytest import mark

from decimal import Decimal
from sqlalchemy_utils import PriceType, types  # noqa
from tests import TestCase


@mark.skipif('types.price.python_price_type is None')
class TestPriceType(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            price = sa.Column(PriceType)

            def __repr__(self):
                return 'Product(%r)' % self.id

        self.Product = Product

    def test_string_parameter_processing(self):
        from prices import Price

        flexmock(PriceType).should_receive('_coerce').and_return(
            '1.99'
        )
        product = self.Product(
            price='1.99'
        )

        self.session.add(product)
        self.session.commit()

        product = self.session.query(self.Product).first()
        assert product.price.net == Price('1.99').net

    def test_decimal_parameter_processing(self):
        from prices import Price

        product = self.Product(
            price=Decimal('1.99')
        )

        self.session.add(product)
        self.session.commit()

        product = self.session.query(self.Product).first()
        assert product.price.net == Price('1.99').net

    def test_price_parameter_processing(self):
        from prices import Price

        product = self.Product(
            price=Price('1.99')
        )

        self.session.add(product)
        self.session.commit()

        product = self.session.query(self.Product).first()
        assert product.price.net == Price('1.99').net

    def test_scalar_attributes_get_coerced_to_objects(self):
        from prices import Price

        product = self.Product(price='1.99')

        assert isinstance(product.price, Price)
