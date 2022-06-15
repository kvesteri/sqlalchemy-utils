import pytest
import sqlalchemy as sa

from sqlalchemy_utils.functions import getdotattr


@pytest.fixture
def Document(Base):
    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
    return Document


@pytest.fixture
def Section(Base, Document):
    class Section(Base):
        __tablename__ = 'section'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

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

        section_id = sa.Column(
            sa.Integer, sa.ForeignKey(Section.id)
        )

        section = sa.orm.relationship(Section, backref='subsections')
    return SubSection


@pytest.fixture
def SubSubSection(Base, SubSection):
    class SubSubSection(Base):
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
    return SubSubSection


@pytest.fixture
def init_models(Document, Section, SubSection, SubSubSection):
    pass


class TestGetDotAttr:

    def test_simple_objects(self, Document, Section, SubSection):
        document = Document(name='some document')
        section = Section(document=document)
        subsection = SubSection(section=section)

        assert getdotattr(
            subsection,
            'section.document.name'
        ) == 'some document'

    def test_with_instrumented_lists(
        self,
        Document,
        Section,
        SubSection,
        SubSubSection
    ):
        document = Document(name='some document')
        section = Section(document=document)
        subsection = SubSection(section=section)
        subsubsection = SubSubSection(subsection=subsection)

        assert getdotattr(document, 'sections') == [section]
        assert getdotattr(document, 'sections.subsections') == [
            subsection
        ]
        assert getdotattr(document, 'sections.subsections.subsubsections') == [
            subsubsection
        ]

    def test_class_paths(self, Document, Section, SubSection):
        assert getdotattr(Section, 'document') is Section.document
        assert (
            getdotattr(SubSection, 'section.document') is
            Section.document
        )
        assert getdotattr(Section, 'document.name') is Document.name
