import sqlalchemy as sa
from sqlalchemy_utils import TSVectorType
from tests import TestCase


class TestTSVector(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            search_index = sa.Column(TSVectorType())

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_generates_table(self):
        assert 'search_index' in self.User.__table__.c

    def test_type_autoloading(self):
        reflected_metadata = sa.schema.MetaData()
        table = sa.schema.Table(
            'user',
            reflected_metadata,
            autoload=True,
            autoload_with=self.engine
        )
        assert isinstance(table.c['search_index'].type, TSVectorType)
