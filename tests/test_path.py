import six
import sqlalchemy as sa
from pytest import mark
from sqlalchemy.util.langhelpers import symbol
from sqlalchemy_utils.path import Path, AttrPath
from tests import TestCase


class TestAttrPath(TestCase):
    def create_models(self):
        class Document(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

        class Section(self.Base):
            __tablename__ = 'section'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

            document_id = sa.Column(
                sa.Integer, sa.ForeignKey(Document.id)
            )

            document = sa.orm.relationship(Document, backref='sections')

        class SubSection(self.Base):
            __tablename__ = 'subsection'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

            section_id = sa.Column(
                sa.Integer, sa.ForeignKey(Section.id)
            )

            section = sa.orm.relationship(Section, backref='subsections')

        self.Document = Document
        self.Section = Section
        self.SubSection = SubSection

    @mark.parametrize(
        ('class_', 'path', 'direction'),
        (
            ('SubSection', 'section', symbol('MANYTOONE')),
        )
    )
    def test_direction(self, class_, path, direction):
        assert (
            AttrPath(getattr(self, class_), path).direction == direction
        )

    def test_invert(self):
        path = ~ AttrPath(self.SubSection, 'section.document')
        assert path.parts == [
            self.Document.sections,
            self.Section.subsections
        ]
        assert str(path.path) == 'sections.subsections'

    def test_len(self):
        len(AttrPath(self.SubSection, 'section.document')) == 2

    def test_init(self):
        path = AttrPath(self.SubSection, 'section.document')
        assert path.class_ == self.SubSection
        assert path.path == Path('section.document')

    def test_iter(self):
        path = AttrPath(self.SubSection, 'section.document')
        assert list(path) == [
            self.SubSection.section,
            self.Section.document
        ]

    def test_repr(self):
        path = AttrPath(self.SubSection, 'section.document')
        assert repr(path) == (
            "AttrPath(SubSection, 'section.document')"
        )

    def test_index(self):
        path = AttrPath(self.SubSection, 'section.document')
        assert path.index(self.Section.document) == 1
        assert path.index(self.SubSection.section) == 0

    def test_getitem(self):
        path = AttrPath(self.SubSection, 'section.document')
        assert path[0] is self.SubSection.section
        assert path[1] is self.Section.document

    def test_getitem_with_slice(self):
        path = AttrPath(self.SubSection, 'section.document')
        assert path[:] == AttrPath(self.SubSection, 'section.document')
        assert path[:-1] == AttrPath(self.SubSection, 'section')
        assert path[1:] == AttrPath(self.Section, 'document')

    def test_eq(self):
        assert (
            AttrPath(self.SubSection, 'section.document') ==
            AttrPath(self.SubSection, 'section.document')
        )
        assert not (
            AttrPath(self.SubSection, 'section') ==
            AttrPath(self.SubSection, 'section.document')
        )

    def test_ne(self):
        assert not (
            AttrPath(self.SubSection, 'section.document') !=
            AttrPath(self.SubSection, 'section.document')
        )
        assert (
            AttrPath(self.SubSection, 'section') !=
            AttrPath(self.SubSection, 'section.document')
        )


class TestPath(object):
    def test_init(self):
        path = Path('attr.attr2')
        assert path.path == 'attr.attr2'

    def test_init_with_path_object(self):
        path = Path(Path('attr.attr2'))
        assert path.path == 'attr.attr2'

    def test_iter(self):
        path = Path('s.s2.s3')
        assert list(path) == ['s', 's2', 's3']

    @mark.parametrize(('path', 'length'), (
        (Path('s.s2.s3'), 3),
        (Path('s.s2'), 2),
        (Path(''), 0)
    ))
    def test_len(self, path, length):
        return len(path) == length

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
        assert six.text_type(Path('s.s2')) == u's.s2'

    def test_getitem_with_slice(self):
        path = Path('s.s2.s3')
        assert path[1:] == Path('s2.s3')

    @mark.parametrize(('test', 'result'), (
        (Path('s.s2') == Path('s.s2'), True),
        (Path('s.s2') == Path('s.s3'), False)
    ))
    def test_eq(self, test, result):
        assert test is result

    @mark.parametrize(('test', 'result'), (
        (Path('s.s2') != Path('s.s2'), False),
        (Path('s.s2') != Path('s.s3'), True)
    ))
    def test_ne(self, test, result):
        assert test is result
