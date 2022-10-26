import os
import warnings

import pytest
import sqlalchemy as sa
import sqlalchemy.event
import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import close_all_sessions

from sqlalchemy_utils import (
    aggregates,
    coercion_listener,
    i18n,
    InstrumentedList
)
from sqlalchemy_utils.compat import (
    _declarative_base,
    _select_args,
    _synonym_for
)
from sqlalchemy_utils.functions.orm import _get_class_registry
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
def postgresql_db_host():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_POSTGRESQL_HOST', 'localhost')


@pytest.fixture(scope='session')
def postgresql_db_user():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_POSTGRESQL_USER', 'postgres')


@pytest.fixture(scope='session')
def postgresql_db_password():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_POSTGRESQL_PASSWORD', '')


@pytest.fixture(scope='session')
def mysql_db_user():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_MYSQL_USER', 'root')


@pytest.fixture
def postgresql_dsn(postgresql_db_user, postgresql_db_password, postgresql_db_host,
                   db_name):
    return 'postgresql://{}:{}@{}/{}'.format(
        postgresql_db_user,
        postgresql_db_password,
        postgresql_db_host,
        db_name
    )


@pytest.fixture
def mysql_dsn(mysql_db_user, db_name):
    return f'mysql+pymysql://{mysql_db_user}@localhost/{db_name}'


@pytest.fixture
def sqlite_memory_dsn():
    return 'sqlite:///:memory:'


@pytest.fixture
def sqlite_none_database_dsn():
    return 'sqlite://'


@pytest.fixture
def sqlite_file_dsn(db_name):
    return f'sqlite:///{db_name}.db'


@pytest.fixture
def mssql_db_user():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_MSSQL_USER', 'sa')


@pytest.fixture
def mssql_db_password():
    return os.environ.get('SQLALCHEMY_UTILS_TEST_MSSQL_PASSWORD',
                          'Strong_Passw0rd')


@pytest.fixture
def mssql_db_driver():
    driver = os.environ.get('SQLALCHEMY_UTILS_TEST_MSSQL_DRIVER',
                            'ODBC Driver 17 for SQL Server')
    return driver.replace(' ', '+')


@pytest.fixture
def mssql_dsn(mssql_db_user, mssql_db_password, mssql_db_driver, db_name):
    return 'mssql+pyodbc://{}:{}@localhost/{}?driver={}'\
        .format(mssql_db_user, mssql_db_password, db_name, mssql_db_driver)


@pytest.fixture
def dsn(request):
    if 'postgresql_dsn' in request.fixturenames:
        return request.getfixturevalue('postgresql_dsn')
    elif 'mysql_dsn' in request.fixturenames:
        return request.getfixturevalue('mysql_dsn')
    elif 'mssql_dsn' in request.fixturenames:
        return request.getfixturevalue('mssql_dsn')
    elif 'sqlite_file_dsn' in request.fixturenames:
        return request.getfixturevalue('sqlite_file_dsn')
    elif 'sqlite_memory_dsn' in request.fixturenames:
        pass  # Return default
    return request.getfixturevalue('sqlite_memory_dsn')


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
    return _declarative_base()


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
            return f'{self.title} {self.name}'

        @full_name.expression
        def full_name(self):
            return sa.func.concat(self.title, ' ', self.name)

        @hybrid_property
        def articles_count(self):
            return len(self.articles)

        @articles_count.expression
        def articles_count(cls):
            Article = _get_class_registry(Base)['Article']
            return (
                sa.select(*_select_args(sa.func.count(Article.id)))
                .where(Article.category_id == cls.id)
                .correlate(Article.__table__)
                .label('article_count')
            )

        @property
        def name_alias(self):
            return self.name

        @_synonym_for('name')
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
    with connection.begin():
        Base.metadata.create_all(connection)
    Session = sessionmaker(bind=connection)
    try:
        # Enable sqlalchemy 2.0 behavior.
        session = Session(future=True)
    except TypeError:
        # sqlalchemy 1.3
        session = Session()
    i18n.get_locale = get_locale

    def teardown():
        aggregates.manager.reset()
        close_all_sessions()
        with connection.begin():
            Base.metadata.drop_all(connection)
        remove_composite_listeners()
        connection.close()
        engine.dispose()

    request.addfinalizer(teardown)

    return session
