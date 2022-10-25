import pytest
import sqlalchemy as sa
from sqlalchemy.util.langhelpers import symbol

from sqlalchemy_utils.path import AttrPath, Path


@pytest.fixture
def Document(Base):
    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        locale = sa.Column(sa.String(10))
    return Document


@pytest.fixture
def Section(Base, Document):
    class Section(Base):
        __tablename__ = 'section'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        locale = sa.Column(sa.String(10))

        document_id = sa.Column(
            sa.Integer, sa.ForeignKey(Document.id)
        )

        document = sa.orm.relationship(Document, backref='sections')
    return Section


@pytest.fixture
def SubSection(Base, Section):
    class SubSection(Base):
        __tablename__ = 'subsection'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        locale = sa.Column(sa.String(10))

        section_id = sa.Column(
            sa.Integer, sa.ForeignKey(Section.id)
        )

        section = sa.orm.relationship(Section, backref='subsections')
    return SubSection


class TestAttrPath:

    @pytest.fixture
    def init_models(self, Document, Section, SubSection):
        pass

    def test_direction(self, SubSection):
        assert (
            AttrPath(SubSection, 'section').direction == symbol('MANYTOONE')
        )

    def test_invert(self, Document, Section, SubSection):
        path = ~ AttrPath(SubSection, 'section.document')
        assert path.parts == [
            Document.sections,
            Section.subsections
        ]
        assert str(path.path) == 'sections.subsections'

    def test_len(self, SubSection):
        len(AttrPath(SubSection, 'section.document')) == 2

    def test_init(self, SubSection):
        path = AttrPath(SubSection, 'section.document')
        assert path.class_ == SubSection
        assert path.path == Path('section.document')

    def test_iter(self, Section, SubSection):
        path = AttrPath(SubSection, 'section.document')
        assert list(path) == [
            SubSection.section,
            Section.document
        ]

    def test_repr(self, SubSection):
        path = AttrPath(SubSection, 'section.document')
        assert repr(path) == (
            "AttrPath(SubSection, 'section.document')"
        )

    def test_index(self, Section, SubSection):
        path = AttrPath(SubSection, 'section.document')
        assert path.index(Section.document) == 1
        assert path.index(SubSection.section) == 0

    def test_getitem(self, Section, SubSection):
        path = AttrPath(SubSection, 'section.document')
        assert path[0] is SubSection.section
        assert path[1] is Section.document

    def test_getitem_with_slice(self, Section, SubSection):
        path = AttrPath(SubSection, 'section.document')
        assert path[:] == AttrPath(SubSection, 'section.document')
        assert path[:-1] == AttrPath(SubSection, 'section')
        assert path[1:] == AttrPath(Section, 'document')

    def test_eq(self, SubSection):
        assert (
            AttrPath(SubSection, 'section.document') ==
            AttrPath(SubSection, 'section.document')
        )
        assert not (
            AttrPath(SubSection, 'section') ==
            AttrPath(SubSection, 'section.document')
        )

    def test_ne(self, SubSection):
        assert not (
            AttrPath(SubSection, 'section.document') !=
            AttrPath(SubSection, 'section.document')
        )
        assert (
            AttrPath(SubSection, 'section') !=
            AttrPath(SubSection, 'section.document')
        )


class TestPath:
    def test_init(self):
        path = Path('attr.attr2')
        assert path.path == 'attr.attr2'

    def test_init_with_path_object(self):
        path = Path(Path('attr.attr2'))
        assert path.path == 'attr.attr2'

    def test_iter(self):
        path = Path('s.s2.s3')
        assert list(path) == ['s', 's2', 's3']

    @pytest.mark.parametrize(('path', 'length'), (
        (Path('s.s2.s3'), 3),
        (Path('s.s2'), 2),
        (Path(''), 1),
    ))
    def test_len(self, path, length):
        assert len(path) == length

    def test_reversed(self):
        path = Path('s.s2.s3')
        assert list(reversed(path)) == ['s3', 's2', 's']

    def test_repr(self):
        path = Path('s.s2')
        assert repr(path) == "Path('s.s2')"

    def test_getitem(self):
        path = Path('s.s2')
        assert path[0] == 's'
        assert path[1] == 's2'

    def test_str(self):
        assert str(Path('s.s2')) == 's.s2'

    def test_index(self):
        assert Path('s.s2.s3').index('s2') == 1

    def test_unicode(self):
        assert str(Path('s.s2')) == 's.s2'

    def test_getitem_with_slice(self):
        path = Path('s.s2.s3')
        assert path[1:] == Path('s2.s3')

    @pytest.mark.parametrize(('test', 'result'), (
        (Path('s.s2') == Path('s.s2'), True),
        (Path('s.s2') == Path('s.s3'), False)
    ))
    def test_eq(self, test, result):
        assert test is result

    @pytest.mark.parametrize(('test', 'result'), (
        (Path('s.s2') != Path('s.s2'), False),
        (Path('s.s2') != Path('s.s3'), True)
    ))
    def test_ne(self, test, result):
        assert test is result
