import os
import warnings

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base, synonym_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import (
    aggregates,
    coercion_listener,
    i18n,
    InstrumentedList
)

from sqlalchemy_utils.types.pg_composite import remove_composite_listeners


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
        territories = {'FI': 'Finland'}

    return Locale()


@pytest.fixture(scope='session')
def db_name():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_DB', 'sqlalchemy_utils_test')


@pytest.fixture(scope='session')
def postgresql_db_user():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_POSTGRESQL_USER', 'postgres')


@pytest.fixture(scope='session')
def mysql_db_user():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_MYSQL_USER', 'root')


@pytest.fixture
def postgresql_dsn(postgresql_db_user, db_name):
    return 'postgres://{0}@localhost/{1}'.format(postgresql_db_user, db_name)


@pytest.fixture
def mysql_dsn(mysql_db_user, db_name):
    return 'mysql+pymysql://{0}@localhost/{1}'.format(mysql_db_user, db_name)


@pytest.fixture
def sqlite_memory_dsn():
    return 'sqlite:///:memory:'


@pytest.fixture
def sqlite_none_database_dsn():
    return 'sqlite://'


@pytest.fixture
def sqlite_file_dsn():
    return 'sqlite:///{0}.db'.format(db_name)


@pytest.fixture
def dsn(request):
    if 'postgresql_dsn' in request.fixturenames:
        return request.getfuncargvalue('postgresql_dsn')
    elif 'mysql_dsn' in request.fixturenames:
        return request.getfuncargvalue('mysql_dsn')
    elif 'sqlite_file_dsn' in request.fixturenames:
        return request.getfuncargvalue('sqlite_file_dsn')
    elif 'sqlite_memory_dsn' in request.fixturenames:
        pass  # Return default
    return request.getfuncargvalue('sqlite_memory_dsn')


@pytest.fixture
def engine(dsn):
    engine = create_engine(dsn)
    # engine.echo = True
    return engine


@pytest.fixture
def connection(engine):
    return engine.connect()


@pytest.fixture
def Base():
    return declarative_base()


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
        name = sa.Column(sa.Unicode(255))
    return User


@pytest.fixture
def Category(Base):

    class Category(Base):
        __tablename__ = 'category'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        title = sa.Column(sa.Unicode(255))

        @hybrid_property
        def full_name(self):
            return u'%s %s' % (self.title, self.name)

        @full_name.expression
        def full_name(self):
            return sa.func.concat(self.title, ' ', self.name)

        @hybrid_property
        def articles_count(self):
            return len(self.articles)

        @articles_count.expression
        def articles_count(cls):
            Article = Base._decl_class_registry['Article']
            return (
                sa.select([sa.func.count(Article.id)])
                .where(Article.category_id == cls.id)
                .correlate(Article.__table__)
                .label('article_count')
            )

        @property
        def name_alias(self):
            return self.name

        @synonym_for('name')
        @property
        def name_synonym(self):
            return self.name
    return Category


@pytest.fixture
def Article(Base, Category):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255), index=True)
        category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

        category = sa.orm.relationship(
            Category,
            primaryjoin=category_id == Category.id,
            backref=sa.orm.backref(
                'articles',
                collection_class=InstrumentedList
            )
        )
    return Article


@pytest.fixture
def init_models(User, Category, Article):
    pass


@pytest.fixture
def session(request, engine, connection, Base, init_models):
    sa.orm.configure_mappers()
    Base.metadata.create_all(connection)
    Session = sessionmaker(bind=connection)
    session = Session()
    i18n.get_locale = get_locale

    def teardown():
        aggregates.manager.reset()
        session.close_all()
        Base.metadata.drop_all(connection)
        remove_composite_listeners()
        connection.close()
        engine.dispose()

    request.addfinalizer(teardown)

    return session
