from sqlalchemy_utils.functions import naturally_equivalent


class TestNaturallyEquivalent(object):
    def test_returns_true_when_properties_match(self, User):
        assert naturally_equivalent(
            User(name=u'someone'), User(name=u'someone')
        )

    def test_skips_primary_keys(self, User):
        assert naturally_equivalent(
            User(id=1, name=u'someone'), User(id=2, name=u'someone')
        )
