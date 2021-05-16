# -*- coding: utf-8 -*-
import pytest
import sqlalchemy as sa

from sqlalchemy_utils.types import json


@pytest.fixture
def Document(Base):
    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        json = sa.Column(json.JSONType)
    return Document


@pytest.fixture
def init_models(Document):
    pass


class JSONTestCase(object):
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
            json={'something': u'äääööö'}
        )

        session.add(document)
        session.commit()

        document = session.query(Document).first()
        assert document.json == {'something': u'äääööö'}

    def test_compilation(self, Document, session):
        query = sa.select([Document.json])
        # the type should be cacheable and not throw exception
        session.execute(query)


@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('sqlite_memory_dsn')
class TestSqliteJSONType(JSONTestCase):
    pass


@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('postgresql_dsn')
class TestPostgresJSONType(JSONTestCase):
    pass
