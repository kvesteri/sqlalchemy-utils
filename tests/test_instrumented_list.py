from tests import TestCase


class TestInstrumentedList(TestCase):
    def test_any_returns_true_if_member_has_attr_defined(self):
        category = self.Category()
        category.articles.append(self.Article())
        category.articles.append(self.Article(name=u'some name'))
        assert category.articles.any('name')

    def test_any_returns_false_if_no_member_has_attr_defined(self):
        category = self.Category()
        category.articles.append(self.Article())
        assert not category.articles.any('name')
