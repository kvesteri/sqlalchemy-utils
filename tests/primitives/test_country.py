from sqlalchemy_utils import Country


class TestCountry(object):
    def test_init(self):
        assert Country(u'fi') == Country(Country(u'fi'))

    def test_equality_operator(self):
        assert Country(u'fi') == u'fi'
        assert u'fi' == Country(u'fi')
        assert Country(u'fi') == Country(u'fi')

    def test_non_equality_operator(self):
        assert Country(u'fi') != u'sv'
        assert not (Country(u'fi') != u'fi')

    def test_hash(self):
        return hash(Country('fi')) == hash('fi')
