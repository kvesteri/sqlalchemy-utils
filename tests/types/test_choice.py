import sqlalchemy as sa
from flexmock import flexmock
from pytest import mark, raises

from sqlalchemy_utils import Choice, ChoiceType, ImproperlyConfigured
from sqlalchemy_utils.types.choice import Enum
from tests import TestCase


class TestChoice(object):
    def test_equality_operator(self):
        assert Choice(1, 1) == 1
        assert 1 == Choice(1, 1)
        assert Choice(1, 1) == Choice(1, 1)

    def test_non_equality_operator(self):
        assert Choice(1, 1) != 2
        assert not (Choice(1, 1) != 1)


class TestChoiceType(TestCase):
    def create_models(self):
        class User(self.Base):
            TYPES = [
                ('admin', 'Admin'),
                ('regular-user', 'Regular user')
            ]

            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            type = sa.Column(ChoiceType(TYPES))

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_python_type(self):
        type_ = self.User.__table__.c.type.type
        assert type_.python_type

    def test_string_processing(self):
        flexmock(ChoiceType).should_receive('_coerce').and_return(
            u'admin'
        )
        user = self.User(
            type=u'admin'
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.type.value == u'Admin'

    def test_parameter_processing(self):
        user = self.User(
            type=u'admin'
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.type.value == u'Admin'

    def test_scalar_attributes_get_coerced_to_objects(self):
        user = self.User(type=u'admin')

        assert isinstance(user.type, Choice)

    def test_throws_exception_if_no_choices_given(self):
        with raises(ImproperlyConfigured):
            ChoiceType([])


class TestChoiceTypeWithCustomUnderlyingType(TestCase):
    def test_init_type(self):
        type_ = ChoiceType([(1, u'something')], impl=sa.Integer)
        assert type_.impl == sa.Integer


@mark.skipif('Enum is None')
class TestEnumType(TestCase):
    def create_models(self):
        class OrderStatus(Enum):
            unpaid = 1
            paid = 2

        class Order(self.Base):
            __tablename__ = 'order'
            id_ = sa.Column(sa.Integer, primary_key=True)
            status = sa.Column(
                ChoiceType(OrderStatus, impl=sa.Integer()),
                default=OrderStatus.unpaid
            )

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
