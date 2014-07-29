import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import get_hybrid_properties


class TestGetHybridProperties(object):
    def setup_method(self, method):
        Base = declarative_base()

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

        self.Category = Category

    def test_declarative_model(self):
        assert (
            list(get_hybrid_properties(self.Category).keys()) ==
            ['lowercase_name']
        )

    def test_mapper(self):
        assert (
            list(get_hybrid_properties(sa.inspect(self.Category)).keys()) ==
            ['lowercase_name']
        )
