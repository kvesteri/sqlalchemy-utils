import sqlalchemy as sa
from sqlalchemy_utils.functions import getdotattr
from tests import TestCase


class TestGetDotAttr(TestCase):
    def create_models(self):
        class Document(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Section(self.Base):
            __tablename__ = 'section'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            document_id = sa.Column(
                sa.Integer, sa.ForeignKey(Document.id)
            )

            document = sa.orm.relationship(Document, backref='sections')

        class SubSection(self.Base):
            __tablename__ = 'subsection'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            section_id = sa.Column(
                sa.Integer, sa.ForeignKey(Section.id)
            )

            section = sa.orm.relationship(Section, backref='subsections')

        class SubSubSection(self.Base):
            __tablename__ = 'subsubsection'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

            subsection_id = sa.Column(
                sa.Integer, sa.ForeignKey(SubSection.id)
            )

            subsection = sa.orm.relationship(
                SubSection, backref='subsubsections'
            )

        self.Document = Document
        self.Section = Section
        self.SubSection = SubSection
        self.SubSubSection = SubSubSection

    def test_simple_objects(self):
        document = self.Document(name=u'some document')
        section = self.Section(document=document)
        subsection = self.SubSection(section=section)

        assert getdotattr(
            subsection,
            'section.document.name'
        ) == u'some document'

    def test_with_instrumented_lists(self):
        document = self.Document(name=u'some document')
        section = self.Section(document=document)
        subsection = self.SubSection(section=section)
        subsubsection = self.SubSubSection(subsection=subsection)

        assert getdotattr(document, 'sections') == [section]
        assert getdotattr(document, 'sections.subsections') == [
            subsection
        ]
        assert getdotattr(document, 'sections.subsections.subsubsections') == [
            subsubsection
        ]

    def test_class_paths(self):
        assert getdotattr(self.Section, 'document') is self.Section.document
        assert (
            getdotattr(self.SubSection, 'section.document') is
            self.Section.document
        )
        assert getdotattr(self.Section, 'document.name') is self.Document.name
