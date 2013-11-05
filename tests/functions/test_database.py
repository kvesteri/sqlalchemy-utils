import sqlalchemy as sa
import os
from tests import TestCase
from sqlalchemy_utils import (
    create_database,
    drop_database,
    database_exists,
)


class DatabaseTest(TestCase):

    def test_create_and_drop(self):
        assert not database_exists(self.url)
        create_database(self.url)
        assert database_exists(self.url)
        drop_database(self.url)
        assert not database_exists(self.url)


class TestDatabaseSQLite(DatabaseTest):

    url = 'sqlite:///sqlalchemy_utils.db'

    def setup(self):
        if os.path.exists('sqlalchemy_utils.db'):
            os.remove('sqlalchemy_utils.db')

    def test_exists_memory(self):
        assert database_exists('sqlite:///:memory:')


class TestDatabaseMySQL(DatabaseTest):
    url = 'mysql+pymysql://travis@localhost/db_test_sqlalchemy_util'


class TestDatabasePostgres(DatabaseTest):
    url = 'postgres://postgres@localhost/db_test_sqlalchemy_util'
