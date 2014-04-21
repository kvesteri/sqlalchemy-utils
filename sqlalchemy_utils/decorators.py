from collections import defaultdict
import itertools
import sqlalchemy as sa
import six
from .functions import getdotattr
from .path import AttrPath


class AttributeValueGenerator(object):
    def __init__(self):
        self.listener_args = [
            (
                sa.orm.mapper,
                'mapper_configured',
                self.update_generator_registry
            ),
            (
                sa.orm.session.Session,
                'before_flush',
                self.update_generated_properties
            )
        ]
        self.reset()

    def reset(self):
        if (
            hasattr(self, 'listeners_registered') and
            self.listeners_registered
        ):
            for args in self.listener_args:
                sa.event.remove(*args)

        self.listeners_registered = False
        # TODO: make the registry a WeakKey dict
        self.generator_registry = defaultdict(list)

    def generator_wrapper(self, func, attr, source):
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        if isinstance(attr, sa.orm.attributes.InstrumentedAttribute):
            self.generator_registry[attr.class_].append(wrapper)
            wrapper.__generates__ = attr, source
        else:
            wrapper.__generates__ = attr, source
        return wrapper

    def register_listeners(self):
        if not self.listeners_registered:
            for args in self.listener_args:
                sa.event.listen(*args)
            self.listeners_registered = True

    def update_generator_registry(self, mapper, class_):
        """
        Adds generator functions to generator_registry.
        """

        for generator in class_.__dict__.values():
            if hasattr(generator, '__generates__'):
                self.generator_registry[class_].append(generator)

    def update_generated_properties(self, session, ctx, instances):
        for obj in itertools.chain(session.new, session.dirty):
            class_ = obj.__class__
            if class_ in self.generator_registry:
                for func in self.generator_registry[class_]:
                    attr, source = func.__generates__
                    if not isinstance(attr, six.string_types):
                        attr = attr.name

                    if source is None:
                        setattr(obj, attr, func(obj))
                    else:
                        setattr(obj, attr, func(obj, getdotattr(obj, source)))


generator = AttributeValueGenerator()


def generates(attr, source=None, generator=generator):
    """
    Decorator that marks given function as attribute value generator.

    Many times you may have generated property values. Usual cases include
    slugs from names or resized thumbnails from images.

    SQLAlchemy-Utils provides a way to do this easily with `generates`
    decorator:

    ::


        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))

            @generates(slug)
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')


        article = self.Article()
        article.name = u'some article name'
        self.session.add(article)
        self.session.flush()
        assert article.slug == u'some-article-name'


    You can also pass the attribute name as a string argument for `generates`:

    ::

        class Article(Base):
            ...

            @generates('slug')
            def _create_slug(self):
                return self.name.lower().replace(' ', '-')


    These property generators can even be defined outside classes:

    ::


        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            slug = sa.Column(sa.Unicode(255))


        @generates(Article.slug)
        def _create_article_slug(article):
            return article.name.lower().replace(' ', '-')


    Property generators can have sources outside:

    ::


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


    You can also use dotted attribute paths for deep relationship paths:

    ::


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

    """

    generator.register_listeners()

    def wraps(func):
        return generator.generator_wrapper(func, attr, source)
    return wraps
