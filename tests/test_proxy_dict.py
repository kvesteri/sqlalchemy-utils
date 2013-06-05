from flexmock import flexmock
import sqlalchemy as sa
from sqlalchemy_utils import ProxyDict, proxy_dict
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
                return proxy_dict(
                    self,
                    '_translations',
                    ArticleTranslation.locale
                )

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

    def test_contains_efficiency(self):
        article = self.Article()
        self.session.add(article)
        self.session.commit()
        article.id
        query_count = self.connection.query_count
        'en' in article.translations
        'en' in article.translations
        'en' in article.translations
        assert self.connection.query_count == query_count + 1

    def test_getitem_with_none_value_in_cache(self):
        article = self.Article()
        self.session.add(article)
        self.session.commit()
        article.id
        'en' in article.translations
        assert article.translations['en']

    def test_contains(self):
        article = self.Article()
        assert 'en' not in article.translations
        # does not auto-append new translation
        assert 'en' not in article.translations

    def test_committing_session_empties_proxy_dict_cache(self):
        article = self.Article()
        (
            flexmock(ProxyDict)
            .should_receive('fetch')
            .twice()
        )
        self.session.add(article)
        self.session.commit()
        article.translations['en']
        self.session.commit()
        article.translations['en']
