import pytest
import sqlalchemy as sa
from flexmock import flexmock

from sqlalchemy_utils import Choice, ChoiceType, ImproperlyConfigured
from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.types.choice import Enum


class TestChoice:
    def test_equality_operator(self):
        assert Choice(1, 1) == 1
        assert 1 == Choice(1, 1)
        assert Choice(1, 1) == Choice(1, 1)

    def test_non_equality_operator(self):
        assert Choice(1, 1) != 2
        assert not (Choice(1, 1) != 1)

    def test_hash(self):
        assert hash(Choice(1, 1)) == hash(1)


class TestChoiceType:
    @pytest.fixture
    def User(self, Base):
        class User(Base):
            TYPES = [
                ('admin', 'Admin'),
                ('regular-user', 'Regular user')
            ]

            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            type = sa.Column(ChoiceType(TYPES))

            def __repr__(self):
                return 'User(%r)' % self.id

        return User

    @pytest.fixture
    def init_models(self, User):
        pass

    def test_python_type(self, User):
        type_ = User.__table__.c.type.type
        assert type_.python_type

    def test_string_processing(self, session, User):
        flexmock(ChoiceType).should_receive('_coerce').and_return(
            'admin'
        )
        user = User(
            type='admin'
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.type.value == 'Admin'

    def test_parameter_processing(self, session, User):
        user = User(
            type='admin'
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.type.value == 'Admin'

    def test_scalar_attributes_get_coerced_to_objects(self, User):
        user = User(type='admin')

        assert isinstance(user.type, Choice)

    def test_throws_exception_if_no_choices_given(self):
        with pytest.raises(ImproperlyConfigured):
            ChoiceType([])

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.type))
        # the type should be cacheable and not throw exception
        session.execute(query)


class TestChoiceTypeWithCustomUnderlyingType:
    def test_init_type(self):
        type_ = ChoiceType([(1, 'something')], impl=sa.Integer)
        assert type_.impl == sa.Integer


@pytest.mark.skipif('Enum is None')
class TestEnumType:

    @pytest.fixture
    def OrderStatus(self):
        class OrderStatus(Enum):
            unpaid = 0
            paid = 1
        return OrderStatus

    @pytest.fixture
    def Order(self, Base, OrderStatus):

        class Order(Base):
            __tablename__ = 'order'
            id_ = sa.Column(sa.Integer, primary_key=True)
            status = sa.Column(
                ChoiceType(OrderStatus, impl=sa.Integer()),
                default=OrderStatus.unpaid,
            )

            def __repr__(self):
                return f'Order({self.id_!r}, {self.status!r})'

        return Order

    @pytest.fixture
    def OrderNullable(self, Base, OrderStatus):

        class OrderNullable(Base):
            __tablename__ = 'order_nullable'
            id_ = sa.Column(sa.Integer, primary_key=True)
            status = sa.Column(
                ChoiceType(OrderStatus, impl=sa.Integer()),
                nullable=True,
            )

        return OrderNullable

    @pytest.fixture
    def init_models(self, Order, OrderNullable):
        pass

    def test_parameter_initialization(self, session, Order, OrderStatus):
        order = Order()

        session.add(order)
        session.commit()

        order = session.query(Order).first()
        assert order.status is OrderStatus.unpaid
        assert order.status.value == 0

    def test_setting_by_value(self, session, Order, OrderStatus):
        order = Order()
        order.status = 1

        session.add(order)
        session.commit()

        order = session.query(Order).first()
        assert order.status is OrderStatus.paid

    def test_setting_by_enum(self, session, Order, OrderStatus):
        order = Order()
        order.status = OrderStatus.paid

        session.add(order)
        session.commit()

        order = session.query(Order).first()
        assert order.status is OrderStatus.paid

    def test_setting_value_that_resolves_to_none(
        self,
        session,
        Order,
        OrderStatus
    ):
        order = Order()
        order.status = 0

        session.add(order)
        session.commit()

        order = session.query(Order).first()
        assert order.status is OrderStatus.unpaid

    def test_setting_to_wrong_enum_raises_valueerror(self, Order):
        class WrongEnum(Enum):
            foo = 0
            bar = 1

        order = Order()

        with pytest.raises(ValueError):
            order.status = WrongEnum.foo

    def test_setting_to_uncoerceable_type_raises_valueerror(self, Order):
        order = Order()
        with pytest.raises(ValueError):
            order.status = 'Bad value'

    def test_order_nullable_stores_none(self, session, OrderNullable):
        # With nullable=False as in `Order`, a `None` value is always
        # converted to the default value, unless we explicitly set it to
        # sqlalchemy.sql.null(), so we use this class to test our ability
        # to set and retrive `None`.
        order_nullable = OrderNullable()
        assert order_nullable.status is None

        order_nullable.status = None

        session.add(order_nullable)
        session.commit()

        assert order_nullable.status is None
