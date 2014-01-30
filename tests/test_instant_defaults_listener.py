from datetime import datetime
import sqlalchemy as sa
from sqlalchemy_utils.listeners import force_instant_defaults
from tests import TestCase


force_instant_defaults()


class TestInstantDefaultListener(TestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255), default=u'Some article')
            created_at = sa.Column(sa.DateTime, default=datetime.now)

        self.Article = Article

    def test_assigns_defaults_on_object_construction(self):
        article = self.Article()
        assert article.name == u'Some article'

    def test_callables_as_defaults(self):
        article = self.Article()
        assert isinstance(article.created_at, datetime)
