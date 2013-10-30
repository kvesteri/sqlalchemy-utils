from sqlalchemy_utils import escape_like
from tests import TestCase


class TestEscapeLike(TestCase):
    def test_escapes_wildcards(self):
        assert escape_like('_*%') == '*_***%'
