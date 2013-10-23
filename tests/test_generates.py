import sqlalchemy as sa
from sqlalchemy_utils import generates
from tests import TestCase


class TestGeneratesWithBoundMethodAndClassVariableArg(TestCase):
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

    def test_generates_value_before_flush(self):
        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'


class TestGeneratesWithBoundMethodAndStringArg(TestCase):
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

    def test_generates_value_before_flush(self):
        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'


class TestGeneratesWithFunctionAndStringArg(TestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

        @generates('Article.slug')
        def _create_article_slug(self):
            return self.name.lower().replace(' ', '-')

        self.Article = Article

    def test_generates_value_before_flush(self):
        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'


class TestGeneratesWithFunctionAndClassVariableArg(TestCase):
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

    def test_generates_value_before_flush(self):
        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'
