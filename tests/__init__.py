import warnings
import sqlalchemy as sa

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base, synonym_for
from sqlalchemy.ext.hybrid import hybrid_property

from sqlalchemy_utils import (
    InstrumentedList, coercion_listener, aggregates, i18n
)


@sa.event.listens_for(sa.engine.Engine, 'before_cursor_execute')
def count_sql_calls(conn, cursor, statement, parameters, context, executemany):
    try:
        conn.query_count += 1
    except AttributeError:
        conn.query_count = 0


warnings.simplefilter('error', sa.exc.SAWarning)


sa.event.listen(sa.orm.mapper, 'mapper_configured', coercion_listener)


def get_locale():
    class Locale():
        territories = {'fi': 'Finland'}

    return Locale()


class TestCase(object):
    dns = 'sqlite:///:memory:'
    create_tables = True

    def setup_method(self, method):
        self.engine = create_engine(self.dns)
        # self.engine.echo = True
        self.connection = self.engine.connect()
        self.Base = declarative_base()

        self.create_models()
        sa.orm.configure_mappers()
        if self.create_tables:
            self.Base.metadata.create_all(self.connection)

        Session = sessionmaker(bind=self.connection)
        self.session = Session()

        i18n.get_locale = get_locale

    def teardown_method(self, method):
        aggregates.manager.reset()
        self.session.close_all()
        if self.create_tables:
            self.Base.metadata.drop_all(self.connection)
        self.connection.close()
        self.engine.dispose()

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @hybrid_property
            def articles_count(self):
                return len(self.articles)

            @articles_count.expression
            def articles_count(cls):
                return (
                    sa.select([sa.func.count(self.Article.id)])
                    .where(self.Article.category_id == self.Category.id)
                    .correlate(self.Article.__table__)
                    .label('article_count')
                )

            @property
            def name_alias(self):
                return self.name

            @synonym_for('name')
            @property
            def name_synonym(self):
                return self.name

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category,
                primaryjoin=category_id == Category.id,
                backref=sa.orm.backref(
                    'articles',
                    collection_class=InstrumentedList
                )
            )

        self.User = User
        self.Category = Category
        self.Article = Article
