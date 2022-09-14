from datetime import datetime

import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from sqlalchemy_utils import generic_repr, Timestamp


class TestTimestamp:
    @pytest.fixture
    def Article(self, Base):
        class Article(Base, Timestamp):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default='Some article')
        return Article

    def test_created(self, session, Article):
        then = datetime.utcnow()
        article = Article()

        session.add(article)
        session.commit()

        assert article.created >= then and article.created <= datetime.utcnow()

    def test_updated(self, session, Article):
        article = Article()

        session.add(article)
        session.commit()

        then = datetime.utcnow()
        article.name = "Something"

        session.commit()

        assert article.updated >= then and article.updated <= datetime.utcnow()


class TestGenericRepr:
    @pytest.fixture
    def Article(self, Base):
        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default='Some article')
        return Article

    @pytest.fixture
    def Point(self):
        class Point:
            """
            A pair of integers.

            A contrived type that raises an exception when compared to other types.
            """
            def __init__(self, x, y):
                self.x = x
                self.y = y

            def __eq__(self, other):
                # NOTE: this raises an AttributeError when compared with other types
                return self.x == other.x and self.y == other.y

            def __repr__(self):
                return "Point({!r},{!r})".format(self.x, self.y)
        return Point
            
    @pytest.fixture
    def PointTable(self, Base, Point):

        class PointType(sa.types.TypeDecorator):
            """
            Stores a pair of integers as a comma separated string "x,y"
            """

            impl = sa.types.VARCHAR

            def process_bind_param(self, value, dialect):
                if value is not None:
                    return repr(value)
                return value

            def process_result_value(self, value, dialect):
                if value is not None:
                    vals = value.split(",")
                    if len(vals) != 2:
                        raise ValueError("Invalid DB string - should be 'x,y'")
                    try:
                        x = int(vals[0])
                        y = int(vals[1])
                    except TypeError:
                        raise ValueError("Invalid DB string - not valid ints")
                    return Point(x, y)
                return value

        class PointTable(Base):
            __tablename__ = 'point'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default=u'Some point')
            value = sa.Column(PointType)

        return PointTable

    def test_repr(self, Article):
        """Representation of a basic model."""
        Article = generic_repr(Article)
        article = Article(id=1, name='Foo')
        expected_repr = "Article(id=1, name='Foo')"
        actual_repr = repr(article)

        assert actual_repr == expected_repr

    def test_repr_partial(self, Article):
        """Representation of a basic model with selected fields."""
        Article = generic_repr('id')(Article)
        article = Article(id=1, name='Foo')
        expected_repr = 'Article(id=1)'
        actual_repr = repr(article)

        assert actual_repr == expected_repr

    def test_not_loaded(self, session, Article):
        """:py:func:`~sqlalchemy_utils.models.generic_repr` doesn't force
        execution of additional queries if some fields are not loaded and
        instead represents them as "<not loaded>".
        """
        Article = generic_repr(Article)
        article = Article(name='Foo')
        session.add(article)
        session.commit()

        article = session.query(Article).options(sa.orm.defer(Article.name)).one()
        actual_repr = repr(article)

        expected_repr = 'Article(id={}, name=<not loaded>)'.format(article.id)
        assert actual_repr == expected_repr

    def test_repr_weird_eq(self, PointTable, Point):
        """:py:func:`~sqlalchemy_utils.models.generic_repr` uses ``is`` to
        check if a field is not loaded, instead of ``==``, which can have
        side-effects."""
        PointTable = generic_repr(PointTable)

        table = PointTable(id=1, name=u'Foo', value=Point(5,4))
        actual_repr = repr(table)
        if sys.version_info[0] == 2:
            expected_repr = u'PointTable(id=1, name=u\'Foo\', value=Point(5,4))'
        elif sys.version_info[0] == 3:
            expected_repr = u'PointTable(id=1, name=\'Foo\', value=Point(5,4))'
        else:
            raise AssertionError
        assert actual_repr == expected_repr
