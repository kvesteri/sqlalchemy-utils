from flexmock import flexmock
from pytest import mark
import sqlalchemy as sa
from sqlalchemy_utils import ColorType
from sqlalchemy_utils.types import color
from tests import TestCase


@mark.skipif('color.python_colour_type is None')
class TestColorType(TestCase):
    def create_models(self):
        class Document(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            bg_color = sa.Column(ColorType)

            def __repr__(self):
                return 'Document(%r)' % self.id

        self.Document = Document

    def test_string_parameter_processing(self):
        from colour import Color

        flexmock(ColorType).should_receive('_coerce').and_return(
            u'white'
        )
        document = self.Document(
            bg_color='white'
        )

        self.session.add(document)
        self.session.commit()

        document = self.session.query(self.Document).first()
        assert document.bg_color.hex == Color(u'white').hex

    def test_color_parameter_processing(self):
        from colour import Color

        document = self.Document(
            bg_color=Color(u'white')
        )

        self.session.add(document)
        self.session.commit()

        document = self.session.query(self.Document).first()
        assert document.bg_color.hex == Color(u'white').hex

    def test_scalar_attributes_get_coerced_to_objects(self):
        from colour import Color

        document = self.Document(bg_color='white')

        assert isinstance(document.bg_color, Color)
