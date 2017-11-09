# -*- coding: utf-8 -*-
import pytest
import sqlalchemy as sa

from sqlalchemy_utils.types import json

try:
    import jsonschema
except ImportError:
    jsonschema = None


@pytest.fixture
def schema():
    return {
        'oneOf': [
            {'type': 'array', 'items': {'type': 'number'}},
            {'type': 'object', 'properties': {'something': {'oneOf': [
                {'type': 'number'},
                {'type': 'string'},
            ]}}},
        ]
    }


@pytest.fixture
def Document(Base, schema):
    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        json = sa.Column(json.JSONType(schema=schema))
    return Document


@pytest.fixture
def CustomValidatorDocument(Base, schema):
    class CustomValidator(jsonschema.validators.Draft4Validator):
        def __init__(self, *args, **kwargs):
            self.call_count = 0
            super(CustomValidator, self).__init__(*args, **kwargs)

        def validate(self, *args, **kwargs):
            self.call_count += 1
            super(CustomValidator, self).validate(*args, **kwargs)

    validator = CustomValidator(schema)

    class CustomValidatorDocument(Base):
        __tablename__ = 'custom_document'
        id = sa.Column(sa.Integer, primary_key=True)
        json = sa.Column(json.JSONType(schema=schema, validator=validator))
        _validator = validator

    return CustomValidatorDocument


@pytest.fixture
def init_models(Document, CustomValidatorDocument):
    pass


@pytest.mark.skipif('jsonschema is None')
class JSONSchemaTestCase(object):

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

    def test_schema_validate(self, session, Document):
        document = Document(json='something')

        session.add(document)

        with pytest.raises(sa.exc.StatementError):
            session.commit()

    def test_custom_validator(self, session, CustomValidatorDocument):
        custom_document = CustomValidatorDocument(json='something')
        validator = CustomValidatorDocument._validator

        session.add(custom_document)

        assert validator.call_count == 0
        with pytest.raises(sa.exc.StatementError):
            session.commit()
        assert validator.call_count == 1

        session.rollback()

        custom_document.json = {'something': 1}
        session.add(custom_document)
        session.commit()
        assert validator.call_count == 2


@pytest.mark.skipif('jsonschema is None')
@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('sqlite_memory_dsn')
class TestSqliteJSONType(JSONSchemaTestCase):
    pass


@pytest.mark.skipif('jsonschema is None')
@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('postgresql_dsn')
class TestPostgresJSONType(JSONSchemaTestCase):
    pass
