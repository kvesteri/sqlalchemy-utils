from sqlalchemy_utils.functions import naturally_equivalent
from tests import TestCase


class TestNaturallyEquivalent(TestCase):
    def test_returns_true_when_properties_match(self):
        assert naturally_equivalent(
            self.User(name=u'someone'), self.User(name=u'someone')
        )

    def test_skips_primary_keys(self):
        assert naturally_equivalent(
            self.User(id=1, name=u'someone'), self.User(id=2, name=u'someone')
        )
