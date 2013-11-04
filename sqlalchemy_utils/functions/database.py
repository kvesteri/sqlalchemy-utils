from sqlalchemy.engine.url import make_url
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError, OperationalError
import os


def database_exists(url):
    """Check if a database exists.
    """

    url = make_url(url)
    database = url.database
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


def create_database(url, encoding='utf8'):
    """Issue the appropriate CREATE DATABASE statement.
    """

    url = make_url(url)

    database = url.database
    if not url.drivername.startswith('sqlite'):
        url.database = None

    engine = sa.create_engine(url)

    if engine.dialect.name == 'postgresql':
        text = "CREATE DATABASE %s ENCODING = '%s'" % (database, encoding)
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
    """

    url = make_url(url)

    database = url.database
    if not url.drivername.startswith('sqlite'):
        url.database = None

    engine = sa.create_engine(url)

    if engine.dialect.name == 'sqlite' and url.database != ':memory:':
        os.remove(url.database)

    else:
        text = "DROP DATABASE %s" % database
        engine.execute(text)
