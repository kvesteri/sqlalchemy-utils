from pytest import raises
import sqlalchemy as sa

from sqlalchemy_utils.functions.sort_query import make_order_by_deterministic

from tests import assert_contains, TestCase


class TestMakeOrderByDeterministic(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode)
            email = sa.Column(sa.Unicode, unique=True)

            email_lower = sa.orm.column_property(
                sa.func.lower(name)
            )

        self.User = User

    def test_column_property(self):
        query = self.session.query(self.User).order_by(self.User.email_lower)
        with raises(TypeError):
            make_order_by_deterministic(query)

    def test_unique_column(self):
        query = self.session.query(self.User).order_by(self.User.email)
        query = make_order_by_deterministic(query)

        assert str(query).endswith('ORDER BY "user".email')

    def test_non_unique_column(self):
        query = self.session.query(self.User).order_by(self.User.name)
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY "user".name, "user".id ASC', query)

    def test_descending_order_by(self):
        query = self.session.query(self.User).order_by(
            sa.desc(self.User.name)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY "user".name DESC, "user".id DESC', query)

    def test_ascending_order_by(self):
        query = self.session.query(self.User).order_by(
            sa.asc(self.User.name)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY "user".name ASC, "user".id ASC', query)
