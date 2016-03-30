import pytest
import sqlalchemy as sa
from flexmock import flexmock
from sqlalchemy.dialects.postgresql import HSTORE

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
class TestTranslationHybrid(object):

    def test_using_hybrid_as_constructor(self, City):
        city = City(name='Helsinki')
        assert city.name_translations['fi'] == 'Helsinki'

    def test_if_no_translation_exists_returns_none(self, City):
        city = City()
        assert city.name is None

    def test_custom_default_value(self, City, translation_hybrid):
        translation_hybrid.default_value = 'Some value'
        city = City()
        assert city.name is 'Some value'

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
            in str(Article.name)
        )

    def test_locales_casted_only_in_compilation_phase(self, Base):
        class LocaleGetter(object):
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

    def test_column_labeling(self, session, City):
        expected = ("coalesce(city.name_translations -> 'fi', "
                    "city.name_translations -> 'en') AS name")
        assert expected in str(session.query(City.name))

    def test_result_object_asdict_keys(self, session, City):
        city = City(
            name_translations={'en': 'Stockholm', 'fi': 'Tukholma'}
        )
        session.add(city)
        session.commit()
        dct = session.query(City.name).first()._asdict()
        assert dct['name'] == 'Tukholma'
