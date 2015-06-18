import sqlalchemy as sa
from flexmock import flexmock
from pytest import mark
from sqlalchemy.dialects.postgresql import HSTORE

from sqlalchemy_utils import i18n, TranslationHybrid  # noqa
from tests import TestCase


@mark.skipif('i18n.babel is None')
class TestTranslationHybrid(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class City(self.Base):
            __tablename__ = 'city'
            id = sa.Column(sa.Integer, primary_key=True)
            name_translations = sa.Column(HSTORE)
            name = self.translation_hybrid(name_translations)
            locale = 'en'

        self.City = City

    def setup_method(self, method):
        self.translation_hybrid = TranslationHybrid('fi', 'en')
        TestCase.setup_method(self, method)

    def test_using_hybrid_as_constructor(self):
        city = self.City(name='Helsinki')
        assert city.name_translations['fi'] == 'Helsinki'

    def test_if_no_translation_exists_returns_none(self):
        city = self.City()
        assert city.name is None

    def test_custom_default_value(self):
        self.translation_hybrid.default_value = 'Some value'
        city = self.City()
        assert city.name is 'Some value'

    def test_fall_back_to_default_translation(self):
        city = self.City(name_translations={'en': 'Helsinki'})
        self.translation_hybrid.current_locale = 'sv'
        assert city.name == 'Helsinki'

    def test_fallback_to_dynamic_locale(self):
        self.translation_hybrid.current_locale = 'en'
        self.translation_hybrid.default_locale = lambda self: self.locale
        city = self.City(name_translations={})
        city.locale = 'fi'
        city.name_translations['fi'] = 'Helsinki'

        assert city.name == 'Helsinki'

    @mark.parametrize(
        ('name_translations', 'name'),
        (
            ({'fi': 'Helsinki', 'en': 'Helsing'}, 'Helsinki'),
            ({'en': 'Helsinki'}, 'Helsinki'),
            ({'fi': 'Helsinki'}, 'Helsinki'),
            ({}, None),
        )
    )
    def test_hybrid_as_an_expression(self, name_translations, name):
        city = self.City(name_translations=name_translations)
        self.session.add(city)
        self.session.commit()

        assert self.session.query(self.City.name).scalar() == name

    def test_dynamic_locale(self):
        translation_hybrid = TranslationHybrid(
            lambda obj: obj.locale,
            'fi'
        )

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name_translations = sa.Column(HSTORE)
            name = translation_hybrid(name_translations)
            locale = sa.Column(sa.String)

        assert (
            'coalesce(article.name_translations -> article.locale'
            in str(Article.name)
        )

    def test_locales_casted_only_in_compilation_phase(self):
        class LocaleGetter(object):
            def current_locale(self):
                return lambda obj: obj.locale

        flexmock(LocaleGetter).should_receive('current_locale').never()
        translation_hybrid = TranslationHybrid(
            LocaleGetter().current_locale,
            'fi'
        )

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name_translations = sa.Column(HSTORE)
            name = translation_hybrid(name_translations)
            locale = sa.Column(sa.String)

        Article.name
