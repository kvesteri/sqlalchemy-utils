import sqlalchemy as sa
from sqlalchemy_utils import generates
from sqlalchemy_utils.decorators import generator
from tests import TestCase


class GeneratesTestCase(TestCase):
    def test_generates_value_before_flush(self):
        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'


class TestGeneratesWithBoundMethodAndClassVariableArg(GeneratesTestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

            @generates(slug)
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')

        self.Article = Article


class TestGeneratesWithBoundMethodAndStringArg(GeneratesTestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

            @generates('slug')
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')

        self.Article = Article


class TestGeneratesWithFunctionAndClassVariableArg(GeneratesTestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

        @generates(Article.slug)
        def _create_article_slug(self):
            return self.name.lower().replace(' ', '-')

        self.Article = Article
