import pytest
import sqlalchemy as sa
from flexmock import flexmock
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.orm import aliased

from sqlalchemy_utils import i18n, TranslationHybrid  # noqa


@pytest.fixture
def translation_hybrid():
    return TranslationHybrid('fi', 'en')


@pytest.fixture
def City(Base, translation_hybrid):
    class City(Base):
        __tablename__ = 'city'
        id = sa.Column(sa.Integer, primary_key=True)
        name_translations = sa.Column(HSTORE)
        name = translation_hybrid(name_translations)
        locale = 'en'
    return City


@pytest.fixture
def init_models(City):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
@pytest.mark.skipif('i18n.babel is None')
class TestTranslationHybrid:

    def test_using_hybrid_as_constructor(self, City):
        city = City(name='Helsinki')
        assert city.name_translations['fi'] == 'Helsinki'

    def test_if_no_translation_exists_returns_none(self, City):
        city = City()
        assert city.name is None

    def test_custom_default_value(self, City, translation_hybrid):
        translation_hybrid.default_value = 'Some value'
        city = City()
        assert city.name == 'Some value'

    def test_fall_back_to_default_translation(self, City, translation_hybrid):
        city = City(name_translations={'en': 'Helsinki'})
        translation_hybrid.current_locale = 'sv'
        assert city.name == 'Helsinki'

    def test_fallback_to_dynamic_locale(self, City, translation_hybrid):
        translation_hybrid.current_locale = 'en'
        translation_hybrid.default_locale = lambda self: self.locale
        city = City(name_translations={})
        city.locale = 'fi'
        city.name_translations['fi'] = 'Helsinki'

        assert city.name == 'Helsinki'

    def test_fallback_to_attr_dependent_locale(self, City, translation_hybrid):
        translation_hybrid.current_locale = 'en'
        translation_hybrid.default_locale = (
            lambda obj, attr: sorted(getattr(obj, attr).keys())[0]
        )
        city = City(name_translations={})
        city.name_translations['fi'] = 'Helsinki'
        assert city.name == 'Helsinki'
        city.name_translations['de'] = 'Stadt Helsinki'
        assert city.name == 'Stadt Helsinki'

    @pytest.mark.parametrize(
        ('name_translations', 'name'),
        (
            ({'fi': 'Helsinki', 'en': 'Helsing'}, 'Helsinki'),
            ({'en': 'Helsinki'}, 'Helsinki'),
            ({'fi': 'Helsinki'}, 'Helsinki'),
            ({}, None),
        )
    )
    def test_hybrid_as_an_expression(
        self,
        session,
        City,
        name_translations,
        name
    ):
        city = City(name_translations=name_translations)
        session.add(city)
        session.commit()

        assert session.query(City.name).scalar() == name

    def test_dynamic_locale(self, Base):
        translation_hybrid = TranslationHybrid(
            lambda obj: obj.locale,
            'fi'
        )

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name_translations = sa.Column(HSTORE)
            name = translation_hybrid(name_translations)
            locale = sa.Column(sa.String)

        assert (
            'coalesce(article.name_translations -> article.locale'
            in str(Article.name.expression)
        )

    def test_locales_casted_only_in_compilation_phase(self, Base):
        class LocaleGetter:
            def current_locale(self):
                return lambda obj: obj.locale

        flexmock(LocaleGetter).should_receive('current_locale').never()
        translation_hybrid = TranslationHybrid(
            LocaleGetter().current_locale,
            'fi'
        )

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name_translations = sa.Column(HSTORE)
            name = translation_hybrid(name_translations)
            locale = sa.Column(sa.String)

        Article.name

    def test_no_implicit_join_when_using_aliased_entities(self, session, City):
        # Ensure that queried entities are taken from the alias so that
        # there isn't an extra join to the original entity.
        CityAlias = aliased(City)
        query_str = str(session.query(CityAlias.name))
        assert query_str.endswith('FROM city AS city_1')
