from flexmock import flexmock
import sqlalchemy as sa
from sqlalchemy_utils import ProxyDict
from tests import TestCase


class TestProxyDict(TestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'

            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            description = sa.Column(sa.UnicodeText)
            _translations = sa.orm.relationship(
                'ArticleTranslation',
                lazy='dynamic',
                cascade='all, delete-orphan',
                passive_deletes=True,
                backref=sa.orm.backref('parent'),
            )

            @property
            def translations(self):
                try:
                    return self.proxied_translations
                except AttributeError:
                    self.proxied_translations = ProxyDict(
                        self,
                        '_translations',
                        ArticleTranslation,
                        'locale'
                    )
                return self.proxied_translations

        class ArticleTranslation(self.Base):
            __tablename__ = 'article_translation'

            id = sa.Column(
                sa.Integer,
                sa.ForeignKey(Article.id),
                autoincrement=True,
                primary_key=True
            )
            locale = sa.Column(sa.String(10), primary_key=True)
            name = sa.Column(sa.UnicodeText)

        self.Article = Article
        self.ArticleTranslation = ArticleTranslation

    def test_access_key_for_pending_parent(self):
        article = self.Article()
        self.session.add(article)
        assert article.translations['en']

    def test_access_key_for_transient_parent(self):
        article = self.Article()
        assert article.translations['en']

    def test_cache(self):
        article = self.Article()
        (
            flexmock(ProxyDict)
            .should_receive('fetch')
            .once()
        )
        self.session.add(article)
        self.session.commit()
        article.translations['en']
        article.translations['en']

    def test_set_updates_cache(self):
        article = self.Article()
        (
            flexmock(ProxyDict)
            .should_receive('fetch')
            .once()
        )
        self.session.add(article)
        self.session.commit()
        article.translations['en']
        article.translations['en'] = self.ArticleTranslation(
            locale='en',
            name=u'something'
        )
        article.translations['en']
