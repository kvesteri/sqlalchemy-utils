import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import cast_if
from sqlalchemy_utils.compat import get_scalar_subquery


@pytest.fixture(scope='class')
def base():
    return declarative_base()


@pytest.fixture(scope='class')
def article_cls(base):
    class Article(base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        name_synonym = sa.orm.synonym('name')

    return Article


class TestCastIf(object):
    def test_column(self, article_cls):
        expr = article_cls.__table__.c.name
        assert cast_if(expr, sa.String) is expr

    def test_column_property(self, article_cls):
        expr = article_cls.name.property
        assert cast_if(expr, sa.String) is expr

    def test_instrumented_attribute(self, article_cls):
        expr = article_cls.name
        assert cast_if(expr, sa.String) is expr

    def test_synonym(self, article_cls):
        expr = article_cls.name_synonym
        assert cast_if(expr, sa.String) is expr

    def test_scalar_selectable(self, article_cls):
        expr = get_scalar_subquery(sa.select([article_cls.id]))
        assert cast_if(expr, sa.Integer) is expr

    def test_scalar(self):
        assert cast_if('something', sa.String) == 'something'
