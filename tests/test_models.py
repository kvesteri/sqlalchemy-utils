from datetime import datetime
import sqlalchemy as sa
from sqlalchemy_utils import Timestamp
from tests import TestCase


class TestTimestamp(TestCase):

    def create_models(self):
        class Article(self.Base, Timestamp):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default=u'Some article')

        self.Article = Article

    def test_created(self):
        then = datetime.utcnow()
        article = self.Article()

        self.session.add(article)
        self.session.commit()

        assert article.created >= then and article.created <= datetime.utcnow()

    def test_updated(self):
        article = self.Article()

        self.session.add(article)
        self.session.commit()

        then = datetime.utcnow()
        article.name = u"Something"

        self.session.commit()

        assert article.updated >= then and article.updated <= datetime.utcnow()
