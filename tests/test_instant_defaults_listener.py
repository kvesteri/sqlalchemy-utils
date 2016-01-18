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
        name = sa.Column(sa.Unicode(255), default=u'Some article')
        created_at = sa.Column(sa.DateTime, default=datetime.now)
    return Article


class TestInstantDefaultListener(object):

    def test_assigns_defaults_on_object_construction(self, Article):
        article = Article()
        assert article.name == u'Some article'

    def test_callables_as_defaults(self, Article):
        article = Article()
        assert isinstance(article.created_at, datetime)
