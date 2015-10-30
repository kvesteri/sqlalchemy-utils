import sqlalchemy as sa

from sqlalchemy_utils.observer import observes
from tests import TestCase


class TestObservesForOneToManyToOneToMany(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Device(self.Base):
            __tablename__ = 'device'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)

        class Order(self.Base):
            __tablename__ = 'order'
            id = sa.Column(sa.Integer, primary_key=True)

            device_id = sa.Column(
                'device', sa.ForeignKey('device.id'), nullable=False
            )
            device = sa.orm.relationship('Device', backref='orders')

        class SalesInvoice(self.Base):
            __tablename__ = 'sales_invoice'
            id = sa.Column(sa.Integer, primary_key=True)
            order_id = sa.Column(
                'order',
                sa.ForeignKey('order.id'),
                nullable=False
            )
            order = sa.orm.relationship(
                'Order',
                backref=sa.orm.backref(
                    'invoice',
                    uselist=False
                )
            )
            device_name = sa.Column(sa.String)

            @observes('order.device')
            def process_device(self, device):
                self.device_name = device.name

        self.Device = Device
        self.Order = Order
        self.SalesInvoice = SalesInvoice

    def test_observable_root_obj_is_none(self):
        order = self.Order(device=self.Device(name='Something'))
        self.session.add(order)
        self.session.flush()
