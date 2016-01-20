import pytest
import sqlalchemy as sa

from sqlalchemy_utils.observer import observes


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForColumn(object):

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
class TestObservesForColumnWithoutActualChanges(object):

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
