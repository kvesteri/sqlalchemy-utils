import sys
from datetime import datetime

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import generic_repr, Timestamp


class TestTimestamp(object):
    @pytest.fixture
    def Article(self, Base):
        class Article(Base, Timestamp):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default=u'Some article')
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
        article.name = u"Something"

        session.commit()

        assert article.updated >= then and article.updated <= datetime.utcnow()


class TestGenericRepr:
    @pytest.fixture
    def Article(self, Base):
        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default=u'Some article')
        return Article

    def test_repr(self, Article):
        """Representation of a basic model."""
        Article = generic_repr(Article)
        article = Article(id=1, name=u'Foo')
        if sys.version_info[0] == 2:
            expected_repr = u'Article(id=1, name=u\'Foo\')'
        elif sys.version_info[0] == 3:
            expected_repr = u'Article(id=1, name=\'Foo\')'
        else:
            raise AssertionError
        actual_repr = repr(article)

        assert actual_repr == expected_repr

    def test_repr_partial(self, Article):
        """Representation of a basic model with selected fields."""
        Article = generic_repr('id')(Article)
        article = Article(id=1, name=u'Foo')
        expected_repr = u'Article(id=1)'
        actual_repr = repr(article)

        assert actual_repr == expected_repr

    def test_not_loaded(self, session, Article):
        """:py:func:`~sqlalchemy_utils.models.generic_repr` doesn't force
        execution of additional queries if some fields are not loaded and
        instead represents them as "<not loaded>".
        """
        Article = generic_repr(Article)
        article = Article(name=u'Foo')
        session.add(article)
        session.commit()

        article = session.query(Article).options(sa.orm.defer('name')).one()
        actual_repr = repr(article)

        expected_repr = u'Article(id={}, name=<not loaded>)'.format(article.id)
        assert actual_repr == expected_repr
