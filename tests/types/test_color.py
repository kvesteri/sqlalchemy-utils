import pytest
import sqlalchemy as sa
from flexmock import flexmock

from sqlalchemy_utils import ColorType, types  # noqa
from sqlalchemy_utils.compat import _select_args


@pytest.fixture
def Document(Base):
    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        bg_color = sa.Column(ColorType)

        def __repr__(self):
            return 'Document(%r)' % self.id
    return Document


@pytest.fixture
def init_models(Document):
    pass


@pytest.mark.skipif('types.color.python_colour_type is None')
class TestColorType:
    def test_string_parameter_processing(self, session, Document):
        from colour import Color

        flexmock(ColorType).should_receive('_coerce').and_return(
            'white'
        )
        document = Document(
            bg_color='white'
        )

        session.add(document)
        session.commit()

        document = session.query(Document).first()
        assert document.bg_color.hex == Color('white').hex

    def test_color_parameter_processing(self, session, Document):
        from colour import Color

        document = Document(bg_color=Color('white'))
        session.add(document)
        session.commit()

        document = session.query(Document).first()
        assert document.bg_color.hex == Color('white').hex

    def test_scalar_attributes_get_coerced_to_objects(self, Document):
        from colour import Color

        document = Document(bg_color='white')
        assert isinstance(document.bg_color, Color)

    def test_literal_param(self, session, Document):
        clause = Document.bg_color == 'white'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == "document.bg_color = 'white'"

    def test_compilation(self, Document, session):
        query = sa.select(*_select_args(Document.bg_color))
        # the type should be cacheable and not throw exception
        session.execute(query)
