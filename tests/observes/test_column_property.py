import pytest
import sqlalchemy as sa

from sqlalchemy_utils.observer import observes


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForColumn:

    @pytest.fixture
    def Product(self, Base):
        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            price = sa.Column(sa.Integer)

            @observes('price')
            def product_price_observer(self, price):
                self.price = price * 2
        return Product

    @pytest.fixture
    def init_models(self, Product):
        pass

    def test_simple_insert(self, session, Product):
        product = Product(price=100)
        session.add(product)
        session.flush()
        assert product.price == 200


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForColumnWithoutActualChanges:

    @pytest.fixture
    def Product(self, Base):
        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            price = sa.Column(sa.Integer)

            @observes('price')
            def product_price_observer(self, price):
                raise Exception('Trying to change price')
        return Product

    @pytest.fixture
    def init_models(self, Product):
        pass

    def test_only_notifies_observer_on_actual_changes(self, session, Product):
        product = Product()
        session.add(product)
        session.flush()

        with pytest.raises(Exception) as e:
            product.price = 500
            session.commit()
        assert str(e.value) == 'Trying to change price'


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForMultipleColumns:

    @pytest.fixture
    def Order(self, Base):
        class Order(Base):
            __tablename__ = 'order'
            id = sa.Column(sa.Integer, primary_key=True)
            unit_price = sa.Column(sa.Integer)
            amount = sa.Column(sa.Integer)
            total_price = sa.Column(sa.Integer)

            @observes('amount', 'unit_price')
            def total_price_observer(self, amount, unit_price):
                self.total_price = amount * unit_price
        return Order

    @pytest.fixture
    def init_models(self, Order):
        pass

    def test_only_notifies_observer_on_actual_changes(self, session, Order):
        order = Order()
        order.amount = 2
        order.unit_price = 10
        session.add(order)
        session.flush()

        order.amount = 1
        session.flush()
        assert order.total_price == 10

        order.unit_price = 100
        session.flush()
        assert order.total_price == 100


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForMultipleColumnsFiresOnlyOnce:

    @pytest.fixture
    def Order(self, Base):
        class Order(Base):
            __tablename__ = 'order'
            id = sa.Column(sa.Integer, primary_key=True)
            unit_price = sa.Column(sa.Integer)
            amount = sa.Column(sa.Integer)

            @observes('amount', 'unit_price')
            def total_price_observer(self, amount, unit_price):
                self.call_count = self.call_count + 1
        return Order

    @pytest.fixture
    def init_models(self, Order):
        pass

    def test_only_notifies_observer_on_actual_changes(self, session, Order):
        order = Order()
        order.amount = 2
        order.unit_price = 10
        order.call_count = 0
        session.add(order)
        session.flush()
        assert order.call_count == 1

        order.amount = 1
        order.unit_price = 100
        session.flush()
        assert order.call_count == 2


class TestObservesForBinaryColumn:

    @pytest.fixture
    def Document(self, Base):
        class Document(Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            content = sa.Column(sa.LargeBinary)
            seen = None

            @observes('content')
            def content_observer(self, content):
                self.seen = content
        return Document

    @pytest.fixture
    def init_models(self, Document):
        pass

    @pytest.mark.parametrize('content', (b'abc', bytearray(b'abc'), memoryview(b'abc')))
    def test_observer_receives_the_binary_value(self, session, Document, content):
        document = Document(content=content)
        session.add(document)
        session.flush()
        assert document.seen == b'abc'


class TestObservesForBinaryColumnThroughRelationship:

    @pytest.fixture
    def Attachment(self, Base):
        class Attachment(Base):
            __tablename__ = 'attachment'
            id = sa.Column(sa.Integer, primary_key=True)
            content = sa.Column(sa.LargeBinary)
            document_id = sa.Column(sa.Integer, sa.ForeignKey('document.id'))
        return Attachment

    @pytest.fixture
    def Document(self, Base, Attachment):
        class Document(Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            attachments = sa.orm.relationship(Attachment, backref='document')
            seen = None

            @observes('attachments.content')
            def content_observer(self, contents):
                self.seen = contents
        return Document

    @pytest.fixture
    def init_models(self, Document):
        pass

    def test_observer_receives_each_binary_value(self, session, Document, Attachment):
        document = Document(
            attachments=[Attachment(content=b'abc'), Attachment(content=b'de')]
        )
        session.add(document)
        session.flush()
        assert document.seen == {b'abc', b'de'}
