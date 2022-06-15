class TestInstrumentedList:
    def test_any_returns_true_if_member_has_attr_defined(
        self,
        Category,
        Article
    ):
        category = Category()
        category.articles.append(Article())
        category.articles.append(Article(name='some name'))
        assert category.articles.any('name')

    def test_any_returns_false_if_no_member_has_attr_defined(
        self,
        Category,
        Article
    ):
        category = Category()
        category.articles.append(Article())
        assert not category.articles.any('name')
