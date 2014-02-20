import sqlalchemy as sa
from sqlalchemy_utils import generates
from tests import TestCase


class GeneratesTestCase(TestCase):
    def test_generates_value_before_flush(self):
        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'


class TestGeneratesWithBoundMethodAndClassVariableArg(GeneratesTestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

            @generates(slug)
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')

        self.Article = Article


class TestGeneratesWithBoundMethodAndStringArg(GeneratesTestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

            @generates('slug')
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')

        self.Article = Article


class TestGeneratesWithFunctionAndClassVariableArg(GeneratesTestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

        @generates(Article.slug)
        def _create_article_slug(self):
            return self.name.lower().replace(' ', '-')

        self.Article = Article


class DeepPathGeneratesTestCase(TestCase):
    def test_simple_dotted_source_path(self):
        document = self.Document(name=u'Document 1', locale='en')
        section = self.Section(name=u'Section 1', document=document)

        self.session.add(document)
        self.session.add(section)
        self.session.commit()

        assert section.locale == 'en'

    def test_deep_dotted_source_path(self):
        document = self.Document(name=u'Document 1', locale='en')
        section = self.Section(name=u'Section 1', document=document)
        subsection = self.SubSection(name=u'Section 1', section=section)

        self.session.add(subsection)
        self.session.commit()

        assert subsection.locale == 'en'


class TestGeneratesWithSourcePath(DeepPathGeneratesTestCase):
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

            @generates(locale, source='document')
            def copy_locale(self, document):
                return document.locale

        class SubSection(self.Base):
            __tablename__ = 'subsection'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            locale = sa.Column(sa.String(10))

            section_id = sa.Column(
                sa.Integer, sa.ForeignKey(Section.id)
            )

            section = sa.orm.relationship(Section)

            @generates(locale, source='section.document')
            def copy_locale(self, document):
                return document.locale


        self.Document = Document
        self.Section = Section
        self.SubSection = SubSection
