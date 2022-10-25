import pytest

import sqlalchemy_utils.compat


@pytest.mark.parametrize(
    "version, expected",
    (
        ("2.0.0b3", (2, 0, 0)),
        ("2.0.0b", (2, 0, 0)),
        ("2.0.0", (2, 0, 0)),
        ("2.0.", (2, 0)),
        ("2.0", (2, 0)),
        ("2.", (2,)),
        ("2", (2,)),
        ("", ()),
    ),
)
def test_get_sqlalchemy_version(version, expected):
    assert sqlalchemy_utils.compat.get_sqlalchemy_version(version) == expected
