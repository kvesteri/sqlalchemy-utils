from colour import Color
import sqlalchemy as sa
from sqlalchemy_utils import ColorType
from tests import TestCase


class TestColorType(TestCase):
    def create_models(self):
        class Document(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            bg_color = sa.Column(ColorType)

            def __repr__(self):
                return 'Document(%r)' % self.id

        self.Document = Document

    def test_color_parameter_processing(self):
        document = self.Document(
            bg_color=Color(u'white')
        )

        self.session.add(document)
        self.session.commit()

        document = self.session.query(self.Document).first()
        assert document.bg_color.hex == Color(u'white').hex
