import pytest
import sqlalchemy as sa

from sqlalchemy_utils import json_sql
from sqlalchemy_utils.compat import _select_args


@pytest.mark.usefixtures('postgresql_dsn')
class TestJSONSQL:

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
                [sa.select(*_select_args(sa.text('1'))).label('alias')],
                [1]
            )
        )
    )
    def test_compiled_scalars(self, connection, value, result):
        assert result == (
            connection.execute(sa.select(*_select_args(json_sql(value)))).fetchone()[0]
        )
