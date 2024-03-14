import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from datetime import datetime, timezone
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
        then = datetime.now(timezone.utc)
        article = Article()

        session.add(article)
        session.commit()

        assert then <= article.created <= datetime.now(timezone.utc)

    def test_updated(self, session, Article):
        article = Article()

        session.add(article)
        session.commit()

        then = datetime.now(timezone.utc)
        article.name = "Something"

        session.commit()

        assert then <= article.updated <= datetime.now(timezone.utc)


class TestGenericRepr:
    @pytest.fixture
    def Article(self, Base):
        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default='Some article')
        return Article

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

        expected_repr = f'Article(id={article.id}, name=<not loaded>)'
        assert actual_repr == expected_repr
