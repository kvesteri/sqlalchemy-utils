# -*- coding: utf-8 -*-
from pytest import mark
import sqlalchemy as sa
from sqlalchemy_utils.types import json
from tests import TestCase


@mark.skipif('json.json is None')
class TestJSONType(TestCase):
    def create_models(self):
        class Document(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            json = sa.Column(json.JSONType)

        self.Document = Document

    def test_parameter_processing(self):
        document = self.Document(
            json={'something': 12}
        )

        self.session.add(document)
        self.session.commit()

        document = self.session.query(self.Document).first()
        assert document.json == {'something': 12}

    def test_non_ascii_chars(self):
        document = self.Document(
            json={'something': u'äääööö'}
        )

        self.session.add(document)
        self.session.commit()

        document = self.session.query(self.Document).first()
        assert document.json == {'something': u'äääööö'}
