import sqlalchemy as sa
from sqlalchemy_utils.functions import getdotattr
from tests import TestCase



class TestTwoWayAttributeValueGeneration(TestCase):
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

            document = sa.orm.relationship(Document)

        class SubSection(self.Base):
            __tablename__ = 'subsection'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

            section_id = sa.Column(
                sa.Integer, sa.ForeignKey(Section.id)
            )

            section = sa.orm.relationship(Section)

        self.Document = Document
        self.Section = Section
        self.SubSection = SubSection

    def test_getdotattr_for_objects(self):
        document = self.Document(name=u'some document')
        section = self.Section(document=document)
        subsection = self.SubSection(section=section)

        assert getdotattr(
            subsection,
            'section.document.name'
        ) == u'some document'

    def test_getdotattr_for_class_paths(self):
        assert getdotattr(self.Section, 'document') is self.Section.document
        assert (
            getdotattr(self.SubSection, 'section.document') is
            self.Section.document
        )
        assert getdotattr(self.Section, 'document.name') is self.Document.name
