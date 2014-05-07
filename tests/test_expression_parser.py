from sqlalchemy_utils import ExpressionParser
import sqlalchemy as sa
from sqlalchemy.sql.elements import Cast, Null

from . import TestCase


class MyExpressionParser(ExpressionParser):
    def __init__(self, some_class):
        self.parent = some_class

    def column(self, column):
        return getattr(self.parent, column.key)

    def instrumented_attribute(self, column):
        return getattr(self.parent, column.key)


class TestExpressionParser(TestCase):
    create_tables = False

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.parser = MyExpressionParser(self.Category)

    def test_false_expression(self):
        expr = self.parser(self.User.name.isnot(False))
        assert str(expr) == 'category.name IS NOT 0'

    def test_true_expression(self):
        expr = self.parser(self.User.name.isnot(True))
        assert str(expr) == 'category.name IS NOT 1'

    def test_unary_expression(self):
        expr = self.parser(~ self.User.name)
        assert str(expr) == 'NOT category.name'

    def test_in_expression(self):
        expr = self.parser(self.User.name.in_([2, 3]))
        assert str(expr) == 'category.name IN (:name_1, :name_2)'

    def test_boolean_expression(self):
        expr = self.parser(self.User.name == False)
        assert str(expr) == 'category.name = 0'

    def test_label(self):
        expr = self.parser(self.User.name.label('some_name'))
        assert str(expr) == 'category.name'

    def test_like(self):
        expr = self.parser(self.User.name.like(u'something'))
        assert str(expr) == 'category.name LIKE :name_1'

    def test_cast(self):
        expr = self.parser(Cast(self.User.name, sa.UnicodeText))
        assert str(expr) == 'CAST(category.name AS TEXT)'

    def test_case(self):
        expr = self.parser(
            sa.case(
                [
                    (self.User.name == 'wendy', 'W'),
                    (self.User.name == 'jack', 'J')
                ],
                else_='E'
            )
        )
        assert str(expr) == (
            'CASE WHEN (category.name = :name_1) '
            'THEN :param_1 WHEN (category.name = :name_2) '
            'THEN :param_2 ELSE :param_3 END'
        )

    def test_tuple(self):
        expr = self.parser(
            sa.tuple_(self.User.name, 3).in_([(u'someone', 3)])
        )
        assert str(expr) == (
            '(category.name, :param_1) IN ((:param_2, :param_3))'
        )

    def test_null(self):
        expr = self.parser(self.User.name == Null())
        assert str(expr) == 'category.name IS NULL'

    def test_instrumented_attribute(self):
        expr = self.parser(self.User.name)
        assert str(expr) == 'Category.name'
