from datetime import datetime

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.listeners import force_instant_defaults

force_instant_defaults()


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255), default='Some article')
        created_at = sa.Column(sa.DateTime, default=datetime.now)
        _byline = sa.Column(sa.Unicode(255), default='Default byline')

        @property
        def byline(self):
            return self._byline

        @byline.setter
        def byline(self, value):
            self._byline = value

    return Article


class TestInstantDefaultListener:
    def test_assigns_defaults_on_object_construction(self, Article):
        article = Article()
        assert article.name == 'Some article'

    def test_callables_as_defaults(self, Article):
        article = Article()
        assert isinstance(article.created_at, datetime)

    def test_override_default_with_setter_function(self, Article):
        article = Article(byline='provided byline')
        assert article.byline == 'provided byline'
