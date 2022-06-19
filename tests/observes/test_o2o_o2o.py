import pytest
import sqlalchemy as sa

from sqlalchemy_utils.observer import observes


@pytest.fixture
def Device(Base):
    class Device(Base):
        __tablename__ = 'device'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
    return Device


@pytest.fixture
def Order(Base):
    class Order(Base):
        __tablename__ = 'order'
        id = sa.Column(sa.Integer, primary_key=True)

        device_id = sa.Column(
            'device', sa.ForeignKey('device.id'), nullable=False
        )
        device = sa.orm.relationship('Device', backref='orders')
    return Order


@pytest.fixture
def SalesInvoice(Base):
    class SalesInvoice(Base):
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

    return SalesInvoice


@pytest.fixture
def init_models(Device, Order, SalesInvoice):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForOneToManyToOneToMany:

    def test_observable_root_obj_is_none(self, session, Device, Order):
        order = Order(device=Device(name='Something'))
        session.add(order)
        session.flush()
