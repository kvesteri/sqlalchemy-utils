# -*- coding: utf-8 -*-
import pytest
import sqlalchemy as sa
import datetime
import re
from json import JSONEncoder, JSONDecoder

from sqlalchemy_utils.types import json


@pytest.fixture
def Document(Base):
    class Document(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        json = sa.Column(json.JSONType)
    return Document

@pytest.fixture
def CustomJSONEncoder():
    class CustomJSONEncoder(JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.replace(microsecond=0).isoformat()
            return super(CustomJSONEncoder, self).default(obj)
    return CustomJSONEncoder

@pytest.fixture
def CustomJSONDecoder():
    DATETIME_ISO_RE = re.compile(r"""
        (?P<year>\d{4})-
        (?P<month>\d{2})-
        (?P<day>\d{2})T
        (?P<hour>\d{2}):
        (?P<minute>\d{2}):
        (?P<second>\d{2})
    """, re.VERBOSE)

    class CustomJSONDecoder(JSONDecoder):
        def decode(self, obj):
            match = DATETIME_ISO_RE.match(obj)
            if match:
                return datetime.datetime(
                    year=int(match.group('year')),
                    month=int(match.group('month')),
                    day=int(match.group('day')),
                    hour=int(match.group('hour')),
                    minute=int(match.group('minute')),
                    second=int(match.group('second')),
                )
            return super(CustomJSONDecoder, self).decode(obj)
    return CustomJSONDecoder


@pytest.fixture
def DateTimeEnabledDocument(Base, CustomJSONEncoder, CustomJSONDecoder):
    class DateTimeEnabledDocument(Base):
        __tablename__ = 'dt_document'
        id = sa.Column(sa.Integer, primary_key=True)
        json = sa.Column(json.JSONType(
            encode_cls=CustomJSONEncoder, decode_cls=CustomJSONDecoder
        ))
    return DateTimeEnabledDocument


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

    def test_custom_encode_decode_classes(self, session, DateTimeEnabledDocument):
        document = DateTimeEnabledDocument(
            json={'created': datetime.datetime(2016, 1, 19, 9, 15, 18)}
        )

        session.add(document)
        session.commit()

        document = session.query(DateTimeEnabledDocument).first()
        assert document.json == {
            'created': datetime.datetime(2016, 1, 19, 9, 15, 18)
        }


@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('sqlite_memory_dsn')
class TestSqliteJSONType(JSONTestCase):
    pass


@pytest.mark.skipif('json.json is None')
@pytest.mark.usefixtures('postgresql_dsn')
class TestPostgresJSONType(JSONTestCase):
    pass
