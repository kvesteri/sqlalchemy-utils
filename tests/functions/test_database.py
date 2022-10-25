import pytest
import sqlalchemy as sa

from sqlalchemy_utils import create_database, database_exists, drop_database

pymysql = None
try:
    import pymysql  # noqa
except ImportError:
    pass


class DatabaseTest:
    def test_create_and_drop(self, dsn):
        assert not database_exists(dsn)
        create_database(dsn)
        assert database_exists(dsn)
        drop_database(dsn)
        assert not database_exists(dsn)


@pytest.mark.usefixtures('sqlite_memory_dsn')
class TestDatabaseSQLiteMemory:

    def test_exists_memory(self, dsn):
        assert database_exists(dsn)


@pytest.mark.usefixtures('sqlite_none_database_dsn')
class TestDatabaseSQLiteMemoryNoDatabaseString:
    def test_exists_memory_none_database(self, sqlite_none_database_dsn):
        assert database_exists(sqlite_none_database_dsn)


@pytest.mark.usefixtures('sqlite_file_dsn')
class TestDatabaseSQLiteFile(DatabaseTest):
    def test_existing_non_sqlite_file(self, dsn):
        database = sa.engine.url.make_url(dsn).database
        open(database, 'w').close()
        self.test_create_and_drop(dsn)


@pytest.mark.skipif('pymysql is None')
@pytest.mark.usefixtures('mysql_dsn')
class TestDatabaseMySQL(DatabaseTest):

    @pytest.fixture
    def db_name(self):
        return 'db_test_sqlalchemy_util'


@pytest.mark.skipif('pymysql is None')
@pytest.mark.usefixtures('mysql_dsn')
class TestDatabaseMySQLWithQuotedName(DatabaseTest):

    @pytest.fixture
    def db_name(self):
        return 'db_test_sqlalchemy-util'


@pytest.mark.usefixtures('postgresql_dsn')
class TestDatabasePostgres(DatabaseTest):

    @pytest.fixture
    def db_name(self):
        return 'db_test_sqlalchemy_util'

    def test_template(self, postgresql_db_user, postgresql_db_password):
        dsn = 'postgresql://{}:{}@localhost/db_test_sqlalchemy_util'.format(
            postgresql_db_user,
            postgresql_db_password
        )
        with pytest.raises(sa.exc.ProgrammingError) as excinfo:
            create_database(dsn, template='my_template')
        assert ("CREATE DATABASE db_test_sqlalchemy_util ENCODING 'utf8' "
                "TEMPLATE my_template") in str(excinfo.value)


class TestDatabasePostgresPg8000(DatabaseTest):

    @pytest.fixture
    def dsn(self, postgresql_db_user, postgresql_db_password):
        return 'postgresql+pg8000://{}:{}@localhost/{}'.format(
            postgresql_db_user,
            postgresql_db_password,
            'db_to_test_create_and_drop_via_pg8000_driver'
        )


class TestDatabasePostgresPsycoPG2CFFI(DatabaseTest):

    @pytest.fixture
    def dsn(self, postgresql_db_user, postgresql_db_password):
        return 'postgresql+psycopg2cffi://{}:{}@localhost/{}'.format(
            postgresql_db_user,
            postgresql_db_password,
            'db_to_test_create_and_drop_via_psycopg2cffi_driver'
        )


@pytest.mark.usefixtures('postgresql_dsn')
class TestDatabasePostgresWithQuotedName(DatabaseTest):

    @pytest.fixture
    def db_name(self):
        return 'db_test_sqlalchemy-util'

    def test_template(self, postgresql_db_user, postgresql_db_password):
        dsn = 'postgresql://{}:{}@localhost/db_test_sqlalchemy-util'.format(
            postgresql_db_user,
            postgresql_db_password
        )
        with pytest.raises(sa.exc.ProgrammingError) as excinfo:
            create_database(dsn, template='my-template')
        assert ('CREATE DATABASE "db_test_sqlalchemy-util" ENCODING \'utf8\' '
                'TEMPLATE "my-template"') in str(excinfo.value)


class TestDatabasePostgresCreateDatabaseCloseConnection:
    def test_create_database_twice(
        self,
        postgresql_db_user,
        postgresql_db_password
    ):
        dsn_list = [
            'postgresql://{}:{}@localhost/db_test_sqlalchemy-util-a'.format(
                postgresql_db_user,
                postgresql_db_password
            ),
            'postgresql://{}:{}@localhost/db_test_sqlalchemy-util-b'.format(
                postgresql_db_user,
                postgresql_db_password
            ),
        ]
        for dsn_item in dsn_list:
            assert not database_exists(dsn_item)
            create_database(dsn_item, template="template1")
            assert database_exists(dsn_item)
        for dsn_item in dsn_list:
            drop_database(dsn_item)
            assert not database_exists(dsn_item)


@pytest.mark.usefixtures('mssql_dsn')
class TestDatabaseMssql(DatabaseTest):

    @pytest.fixture
    def db_name(self):
        pytest.importorskip('pyodbc')
        return 'db_test_sqlalchemy_util'
