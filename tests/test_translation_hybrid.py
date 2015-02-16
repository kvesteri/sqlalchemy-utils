import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy_utils import TranslationHybrid

from tests import TestCase


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

    def test_hybrid_as_expression(self):
        assert self.City.name == self.City.name_translations

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

    def test_hybrid_as_an_expression(self):
        city = self.City(name_translations={'en': 'Helsinki'})
        self.session.add(city)
        self.session.commit()

        assert city == self.session.query(self.City).filter(
            self.City.name['en'] == 'Helsinki'
        ).first()
