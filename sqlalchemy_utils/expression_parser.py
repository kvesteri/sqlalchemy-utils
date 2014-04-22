import six
import sqlalchemy as sa
from sqlalchemy.sql.annotation import AnnotatedColumn
from sqlalchemy.sql.expression import (
    BooleanClauseList,
    BinaryExpression,
    UnaryExpression,
    BindParameter,
    Cast,
)
from sqlalchemy.sql.elements import (
    False_,
    True_,
    Grouping,
    ClauseList,
    Label,
    Case,
    Tuple,
    Null
)


class ExpressionParser(object):
    def expression(self, expr):
        if expr is None:
            return
        if isinstance(expr, BinaryExpression):
            return self.binary_expression(expr)
        elif isinstance(expr, BooleanClauseList):
            return self.boolean_expression(expr)
        elif isinstance(expr, UnaryExpression):
            return self.unary_expression(expr)
        elif isinstance(expr, sa.Column):
            return self.column(expr)
        elif isinstance(expr, AnnotatedColumn):
            return self.column(expr)
        elif isinstance(expr, BindParameter):
            return self.bind_parameter(expr)
        elif isinstance(expr, False_):
            return self.false(expr)
        elif isinstance(expr, True_):
            return self.true(expr)
        elif isinstance(expr, Grouping):
            return self.grouping(expr)
        elif isinstance(expr, ClauseList):
            return self.clause_list(expr)
        elif isinstance(expr, Label):
            return self.label(expr)
        elif isinstance(expr, Cast):
            return self.cast(expr)
        elif isinstance(expr, Case):
            return self.case(expr)
        elif isinstance(expr, Tuple):
            return self.tuple(expr)
        elif isinstance(expr, Null):
            return self.null(expr)
        raise Exception(
            'Unknown expression type %s' % expr.__class__.__name__
        )

    def null(self, expr):
        return expr

    def tuple(self, expr):
        return expr.__class__(
            *map(self.expression, expr.clauses),
            type_=expr.type
        )

    def clause_list(self, expr):
        return expr.__class__(
            *map(self.expression, expr.clauses),
            group=expr.group,
            group_contents=expr.group_contents,
            operator=expr.operator
        )

    def label(self, expr):
        return expr.__class__(
            name=expr.name,
            element=self.expression(expr._element),
            type_=expr.type
        )

    def cast(self, expr):
        return expr.__class__(
            expression=self.expression(expr.clause),
            type_=expr.type
        )

    def case(self, expr):
        return expr.__class__(
            whens=[
                tuple(self.expression(x) for x in when) for when in expr.whens
            ],
            value=self.expression(expr.value),
            else_=self.expression(expr.else_)
        )

    def grouping(self, expr):
        return expr.__class__(self.expression(expr.element))

    def true(self, expr):
        return expr

    def false(self, expr):
        return expr

    def process_table(self, table):
        return table

    def column(self, column):
        table = self.process_table(column.table)
        return table.c[column.name]

    def unary_expression(self, expr):
        return expr.operator(self.expression(expr.element))

    def bind_parameter(self, expr):
        # somehow bind parameters passed as unicode are converted to
        # ascii strings along the way, force convert them back to avoid
        # sqlalchemy unicode warnings
        if isinstance(expr.type, sa.Unicode):
            expr.value = six.text_type(expr.value)
        return expr

    def binary_expression(self, expr):
        return expr.__class__(
            left=self.expression(expr.left),
            right=self.expression(expr.right),
            operator=expr.operator,
            type_=expr.type,
            negate=expr.negate,
            modifiers=expr.modifiers.copy()
        )

    def boolean_expression(self, expr):
        return expr.operator(*[
            self.expression(child_expr)
            for child_expr in expr.get_children()
        ])

    def __call__(self, expr):
        return self.expression(expr)
