import os
from copy import copy

import sqlalchemy as sa
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy_utils.expressions import explain_analyze


class PlanAnalysis(object):
    def __init__(self, plan):
        self.plan = plan

    @property
    def node_types(self):
        types = [self.plan['Node Type']]
        if 'Plans' in self.plan:
            for plan in self.plan['Plans']:
                analysis = PlanAnalysis(plan)
                types.extend(analysis.node_types)
        return types


class QueryAnalysis(object):
    def __init__(self, result_set):
        self.plan = result_set[0]['Plan']
        self.runtime = result_set[0]['Total Runtime']

    @property
    def node_types(self):
        return list(PlanAnalysis(self.plan).node_types)

    def __repr__(self):
        return '<QueryAnalysis runtime=%r>' % self.runtime


def analyze(conn, query):
    """
    Analyze query using given connection and return :class:`QueryAnalysis`
    object. Analysis is performed using database specific EXPLAIN ANALYZE
    construct and then examining the results into structured format. Currently
    only PostgreSQL is supported.


    Getting query runtime (in database level) ::


        from sqlalchemy_utils import analyze


        analysis = analyze(conn, 'SELECT * FROM article')
        analysis.runtime  # runtime as milliseconds


    Analyze can be very useful when testing that query doesn't issue a
    sequential scan (scanning all rows in table). You can for example write
    simple performance tests this way.::


        query = (
            session.query(Article.name)
            .order_by(Article.name)
            .limit(10)
        )
        analysis = analyze(self.connection, query)
        analysis.node_types  # [u'Limit', u'Index Only Scan']

        assert 'Seq Scan' not in analysis.node_types


    .. versionadded: 0.26.17

    :param conn: SQLAlchemy Connection object
    :param query: SQLAlchemy Query object or query as a string
    """
    return QueryAnalysis(
        conn.execute(
            explain_analyze(query, buffers=True, format='json')
        ).scalar()
    )


def escape_like(string, escape_char='*'):
    """
    Escape the string paremeter used in SQL LIKE expressions.

    ::

        from sqlalchemy_utils import escape_like


        query = session.query(User).filter(
            User.name.ilike(escape_like('John'))
        )


    :param string: a string to escape
    :param escape_char: escape character
    """
    return (
        string
        .replace(escape_char, escape_char * 2)
        .replace('%', escape_char + '%')
        .replace('_', escape_char + '_')
    )


def has_index(column):
    """
    Return whether or not given column has an index. A column has an index if
    it has a single column index or it is the first column in compound column
    index.

    :param column: SQLAlchemy Column object

    .. versionadded: 0.26.2

    ::

        from sqlalchemy_utils import has_index


        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            title = sa.Column(sa.String(100))
            is_published = sa.Column(sa.Boolean, index=True)
            is_deleted = sa.Column(sa.Boolean)
            is_archived = sa.Column(sa.Boolean)

            __table_args__ = (
                sa.Index('my_index', is_deleted, is_archived),
            )


        table = Article.__table__

        has_index(table.c.is_published) # True
        has_index(table.c.is_deleted)   # True
        has_index(table.c.is_archived)  # False


    Also supports primary key indexes

    ::

        from sqlalchemy_utils import has_index


        class ArticleTranslation(Base):
            __tablename__ = 'article_translation'
            id = sa.Column(sa.Integer, primary_key=True)
            locale = sa.Column(sa.String(10), primary_key=True)
            title = sa.Column(sa.String(100))


        table = ArticleTranslation.__table__

        has_index(table.c.locale)   # False
        has_index(table.c.id)       # True
    """
    table = column.table
    if not isinstance(table, sa.Table):
        raise TypeError(
            'Only columns belonging to Table objects are supported. Given '
            'column belongs to %r.' % table
        )
    return (
        column is table.primary_key.columns.values()[0]
        or
        any(
            index.columns.values()[0] is column
            for index in table.indexes
        )
    )


def has_unique_index(column):
    """
    Return whether or not given column has a unique index. A column has a
    unique index if it has a single column primary key index or it has a
    single column UniqueConstraint.

    :param column: SQLAlchemy Column object

    .. versionadded: 0.27.1

    ::

        from sqlalchemy_utils import has_unique_index


        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            title = sa.Column(sa.String(100))
            is_published = sa.Column(sa.Boolean, unique=True)
            is_deleted = sa.Column(sa.Boolean)
            is_archived = sa.Column(sa.Boolean)


        table = Article.__table__

        has_unique_index(table.c.is_published) # True
        has_unique_index(table.c.is_deleted)   # False
        has_unique_index(table.c.id)           # True


    :raises TypeError: if given column does not belong to a Table object
    """
    table = column.table
    if not isinstance(table, sa.Table):
        raise TypeError(
            'Only columns belonging to Table objects are supported. Given '
            'column belongs to %r.' % table
        )
    pks = table.primary_key.columns
    return (
        (column is pks.values()[0] and len(pks) == 1)
        or
        any(
            match_columns(constraint.columns.values()[0], column) and
            len(constraint.columns) == 1
            for constraint in column.table.constraints
            if isinstance(constraint, sa.sql.schema.UniqueConstraint)
        )
    )


def match_columns(column, column2):
    return column.table is column2.table and column.name == column2.name


def is_auto_assigned_date_column(column):
    """
    Returns whether or not given SQLAlchemy Column object's is auto assigned
    DateTime or Date.

    :param column: SQLAlchemy Column object
    """
    return (
        (
            isinstance(column.type, sa.DateTime) or
            isinstance(column.type, sa.Date)
        )
        and
        (
            column.default or
            column.server_default or
            column.onupdate or
            column.server_onupdate
        )
    )


def database_exists(url):
    """Check if a database exists.

    :param url: A SQLAlchemy engine URL.

    Performs backend-specific testing to quickly determine if a database
    exists on the server. ::

        database_exists('postgres://postgres@localhost/name')  #=> False
        create_database('postgres://postgres@localhost/name')
        database_exists('postgres://postgres@localhost/name')  #=> True

    Supports checking against a constructed URL as well. ::

        engine = create_engine('postgres://postgres@localhost/name')
        database_exists(engine.url)  #=> False
        create_database(engine.url)
        database_exists(engine.url)  #=> True

    """

    url = copy(make_url(url))
    database = url.database
    if url.drivername.startswith('postgresql'):
        url.database = 'template1'
    else:
        url.database = None

    engine = sa.create_engine(url)

    if engine.dialect.name == 'postgresql':
        text = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
        return bool(engine.execute(text).scalar())

    elif engine.dialect.name == 'mysql':
        text = ("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = '%s'" % database)
        return bool(engine.execute(text).scalar())

    elif engine.dialect.name == 'sqlite':
        return database == ':memory:' or os.path.exists(database)

    else:
        text = 'SELECT 1'
        try:
            url.database = database
            engine = sa.create_engine(url)
            engine.execute(text)
            return True

        except (ProgrammingError, OperationalError):
            return False


def create_database(url, encoding='utf8', template=None):
    """Issue the appropriate CREATE DATABASE statement.

    :param url: A SQLAlchemy engine URL.
    :param encoding: The encoding to create the database as.
    :param template:
        The name of the template from which to create the new database. At the
        moment only supported by PostgreSQL driver.

    To create a database, you can pass a simple URL that would have
    been passed to ``create_engine``. ::

        create_database('postgres://postgres@localhost/name')

    You may also pass the url from an existing engine. ::

        create_database(engine.url)

    Has full support for mysql, postgres, and sqlite. In theory,
    other database engines should be supported.
    """

    url = copy(make_url(url))

    database = url.database

    if url.drivername.startswith('postgresql'):
        url.database = 'template1'
    elif not url.drivername.startswith('sqlite'):
        url.database = None

    engine = sa.create_engine(url)

    if engine.dialect.name == 'postgresql':
        if engine.driver == 'psycopg2':
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            engine.raw_connection().set_isolation_level(
                ISOLATION_LEVEL_AUTOCOMMIT
            )

        if not template:
            template = 'template0'

        text = "CREATE DATABASE %s ENCODING '%s' TEMPLATE %s" % (
            database, encoding, template
        )
        engine.execute(text)

    elif engine.dialect.name == 'mysql':
        text = "CREATE DATABASE %s CHARACTER SET = '%s'" % (database, encoding)
        engine.execute(text)

    elif engine.dialect.name == 'sqlite' and database != ':memory:':
        open(database, 'w').close()

    else:
        text = "CREATE DATABASE %s" % database
        engine.execute(text)


def drop_database(url):
    """Issue the appropriate DROP DATABASE statement.

    :param url: A SQLAlchemy engine URL.

    Works similar to the :ref:`create_database` method in that both url text
    and a constructed url are accepted. ::

        drop_database('postgres://postgres@localhost/name')
        drop_database(engine.url)

    """

    url = copy(make_url(url))

    database = url.database

    if url.drivername.startswith('postgresql'):
        url.database = 'template1'
    elif not url.drivername.startswith('sqlite'):
        url.database = None

    engine = sa.create_engine(url)

    if engine.dialect.name == 'sqlite' and url.database != ':memory:':
        os.remove(url.database)

    elif engine.dialect.name == 'postgresql' and engine.driver == 'psycopg2':
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        engine.raw_connection().set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        # Disconnect all users from the database we are dropping.
        version = list(
            map(
                int,
                engine.execute('SHOW server_version;').first()[0].split('.')
            )
        )
        pid_column = (
            'pid' if (version[0] >= 9 and version[1] >= 2) else 'procpid'
        )
        text = '''
        SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '%(database)s'
          AND %(pid_column)s <> pg_backend_pid();
        ''' % {'pid_column': pid_column, 'database': database}
        engine.execute(text)

        # Drop the database.
        text = "DROP DATABASE %s" % database
        engine.execute(text)

    else:
        text = "DROP DATABASE %s" % database
        engine.execute(text)
