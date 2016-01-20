from datetime import datetime

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import Timestamp


@pytest.fixture
def Article(Base):
    class Article(Base, Timestamp):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255), default=u'Some article')
    return Article


class TestTimestamp(object):

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
