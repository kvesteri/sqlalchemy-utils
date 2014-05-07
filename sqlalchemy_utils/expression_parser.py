try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import six
import sqlalchemy as sa
from sqlalchemy.orm.attributes import InstrumentedAttribute
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
    parsers = OrderedDict((
        (BinaryExpression, 'binary_expression'),
        (BooleanClauseList, 'boolean_expression'),
        (UnaryExpression, 'unary_expression'),
        (sa.Column, 'column'),
        (AnnotatedColumn, 'column'),
        (BindParameter, 'bind_parameter'),
        (False_, 'false'),
        (True_, 'true'),
        (Grouping, 'grouping'),
        (ClauseList, 'clause_list'),
        (Label, 'label'),
        (Cast, 'cast'),
        (Case, 'case'),
        (Tuple, 'tuple'),
        (Null, 'null'),
        (InstrumentedAttribute, 'instrumented_attribute')
    ))

    def expression(self, expr):
        if expr is None:
            return
        for class_, parser in self.parsers.items():
            if isinstance(expr, class_):
                return getattr(self, parser)(expr)
        raise Exception(
            'Unknown expression type %s' % expr.__class__.__name__
        )

    def instrumented_attribute(self, expr):
        return expr

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
