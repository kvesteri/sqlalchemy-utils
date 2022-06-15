import pytest
import sqlalchemy as sa
from flexmock import flexmock

from sqlalchemy_utils import proxy_dict, ProxyDict


@pytest.fixture
def ArticleTranslation(Base):
    class ArticleTranslation(Base):
        __tablename__ = 'article_translation'

        id = sa.Column(
            sa.Integer,
            sa.ForeignKey('article.id'),
            primary_key=True
        )
        locale = sa.Column(sa.String(10), primary_key=True)
        name = sa.Column(sa.UnicodeText)
    return ArticleTranslation


@pytest.fixture
def Article(Base, ArticleTranslation):

    class Article(Base):
        __tablename__ = 'article'

        id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
        description = sa.Column(sa.UnicodeText)
        _translations = sa.orm.relationship(
            ArticleTranslation,
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
    return Article


@pytest.fixture
def init_models(ArticleTranslation, Article):
    pass


class TestProxyDict:

    def test_access_key_for_pending_parent(self, session, Article):
        article = Article()
        session.add(article)
        assert article.translations['en']

    def test_access_key_for_transient_parent(self, Article):
        article = Article()
        assert article.translations['en']

    def test_cache(self, session, Article):
        article = Article()
        (
            flexmock(ProxyDict)
            .should_receive('fetch')
            .once()
        )
        session.add(article)
        session.commit()
        article.translations['en']
        article.translations['en']

    def test_set_updates_cache(self, session, Article, ArticleTranslation):
        article = Article()
        (
            flexmock(ProxyDict)
            .should_receive('fetch')
            .once()
        )
        session.add(article)
        session.commit()
        article.translations['en']
        article.translations['en'] = ArticleTranslation(
            locale='en',
            name='something'
        )
        article.translations['en']

    def test_contains_efficiency(self, connection, session, Article):
        article = Article()
        session.add(article)
        session.commit()
        article.id
        query_count = connection.query_count
        'en' in article.translations
        'en' in article.translations
        'en' in article.translations
        assert connection.query_count == query_count + 1

    def test_getitem_with_none_value_in_cache(self, session, Article):
        article = Article()
        session.add(article)
        session.commit()
        article.id
        'en' in article.translations
        assert article.translations['en']

    def test_contains(self, Article):
        article = Article()
        assert 'en' not in article.translations
        # does not auto-append new translation
        assert 'en' not in article.translations

    def test_committing_session_empties_proxy_dict_cache(
        self,
        session,
        Article
    ):
        article = Article()
        (
            flexmock(ProxyDict)
            .should_receive('fetch')
            .twice()
        )
        session.add(article)
        session.commit()
        article.translations['en']
        session.commit()
        article.translations['en']
