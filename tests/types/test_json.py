import pytest
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.types import json


@pytest.fixture
def Document(Base):
    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        json = sa.Column(json.JSONType)
    return Document


@pytest.fixture
def AAA(Base):
    class AAA(Base):
        __tablename__ = 'aaa'
        id = sa.Column(sa.Integer, primary_key=True)
        json_column = sa.Column(json.JSONType, nullable=False)

    return AAA


@pytest.fixture
def BBB(Base, AAA):
    class BBB(Base):
        __tablename__ = 'bbb'
        id = sa.Column(sa.Integer, primary_key=True)
        aaa_id = sa.Column(sa.Integer, sa.ForeignKey('aaa.id'), nullable=True)
        parent = sa_orm.relationship('AAA', backref='children')

    return BBB


@pytest.fixture
def init_models(Document):
    pass


class JSONTestCase:
    def test_list(self, session, Document):
        document = Document(
            json=[1, 2, 3]
        )

        session.add(document)
        session.commit()

        document = session.query(Document).first()
        assert document.json == [1, 2, 3]

    def test_parameter_processing(self, session, Document):
        document = Document(
            json={'something': 12}
        )

        session.add(document)
        session.commit()

        document = session.query(Document).first()
        assert document.json == {'something': 12}

    def test_non_ascii_chars(self, session, Document):
        document = Document(
            json={'something': 'äääööö'}
        )

        session.add(document)
        session.commit()

        document = session.query(Document).first()
        assert document.json == {'something': 'äääööö'}

    def test_compilation(self, Document, session):
        query = sa.select(*_select_args(Document.json))
        # the type should be cacheable and not throw exception
        session.execute(query)

    def test_unhashable_type(self, AAA, BBB, session):
        """Verify there are no TypeErrors with certain JSON queries.

        This test will fail under these conditions:

        1.  sqlalchemy versions 1.4.19 through 1.4.23 are installed.
        2.  `JSONType.hashable` is not set to False.

        For more info, see:

        *   kvesteri/sqlalchemy-utils#543
        *   sqlalchemy/sqlalchemy#6924
        """

        session.add(AAA(id=13, json_column=[1, 2, 3]))
        session.add(BBB(id=333, aaa_id=13))

        query = session.query(AAA).join(BBB).with_entities(
            AAA.id, AAA.json_column,
        )
        assert len(list(query)) == 1


@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('sqlite_memory_dsn')
class TestSqliteJSONType(JSONTestCase):
    pass


@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('postgresql_dsn')
class TestPostgresJSONType(JSONTestCase):
    pass
