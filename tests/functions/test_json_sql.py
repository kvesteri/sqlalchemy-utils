import pytest
import sqlalchemy as sa
from sqlalchemy_utils import json_sql

from tests import TestCase


class TestJSONSQL(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    @pytest.mark.parametrize(
        ('value', 'result'),
        (
            (1, 1),
            (14.14, 14.14),
            ({'a': 2, 'b': 'c'}, {'a': 2, 'b': 'c'}),
            (
                {'a': {'b': 'c'}},
                {'a': {'b': 'c'}}
            ),
            ({}, {}),
            ([1, 2], [1, 2]),
            ([], []),
            (
                [sa.select([sa.text('1')]).label('alias')],
                [1]
            )
        )
    )
    def test_compiled_scalars(self, value, result):
        assert result == (
            self.connection.execute(sa.select([json_sql(value)])).fetchone()[0]
        )
