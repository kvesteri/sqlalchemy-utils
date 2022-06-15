import pytest
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy_utils import get_hybrid_properties


@pytest.fixture
def Category(Base):
    class Category(Base):
        __tablename__ = 'category'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @hybrid_property
        def lowercase_name(self):
            return self.name.lower()

        @lowercase_name.expression
        def lowercase_name(cls):
            return sa.func.lower(cls.name)
    return Category


class TestGetHybridProperties:

    def test_declarative_model(self, Category):
        assert (
            list(get_hybrid_properties(Category).keys()) ==
            ['lowercase_name']
        )

    def test_mapper(self, Category):
        assert (
            list(get_hybrid_properties(sa.inspect(Category)).keys()) ==
            ['lowercase_name']
        )

    def test_aliased_class(self, Category):
        props = get_hybrid_properties(sa.orm.aliased(Category))
        assert list(props.keys()) == ['lowercase_name']
