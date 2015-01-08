import pytest
import sqlalchemy as sa
from sqlalchemy_utils import json_sql

from tests import TestCase


class TestJSONSQL(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    @pytest.mark.parametrize(
        ('value', 'compiled'),
        (
            (1, 'to_json(1)'),
            (14.14, 'to_json(14.14)'),
            ({'a': 2, 'b': 'c'}, "json_build_object('a', 2, 'b', 'c')"),
            (
                {'a': {'b': 'c'}},
                "json_build_object('a', json_build_object('b', 'c'))"
            ),
            ({}, 'json_build_object()'),
            ([1, 2], 'json_build_array(1, 2)'),
            ([], 'json_build_array()'),
            (
                [sa.select([sa.text('1')])],
                'json_build_array((SELECT 1))'
            )
        )
    )
    def test_compiled_scalars(self, value, compiled):
        assert str(json_sql(value).compile(self.connection)) == compiled
