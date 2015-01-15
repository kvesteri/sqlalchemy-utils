from pytest import mark
import sqlalchemy as sa
from sqlalchemy_utils.types import enum
from tests import TestCase


@mark.skipif('enum.Enum is None')
class TestEnumType(TestCase):
    def create_models(self):
        class OrderStatus(enum.Enum):
            unpaid = 1
            paid = 2

        class Order(self.Base):
            __tablename__ = 'document'
            id_ = sa.Column(sa.Integer, primary_key=True)
            status = sa.Column(
                enum.EnumType(OrderStatus), default=OrderStatus.unpaid)

            def __repr__(self):
                return 'Order(%r, %r)' % (self.id_, self.status)

            def pay(self):
                self.status = OrderStatus.paid

        self.OrderStatus = OrderStatus
        self.Order = Order

    def test_parameter_processing(self):
        order = self.Order()

        self.session.add(order)
        self.session.commit()

        order = self.session.query(self.Order).first()
        assert order.status is self.OrderStatus.unpaid
        assert order.status.value == 1

        order.pay()
        self.session.commit()

        order = self.session.query(self.Order).first()
        assert order.status is self.OrderStatus.paid
        assert order.status.value == 2

    def test_parameter_coercing(self):
        order = self.Order()
        order.status = 2

        self.session.add(order)
        self.session.commit()

        assert order.status is self.OrderStatus.paid
