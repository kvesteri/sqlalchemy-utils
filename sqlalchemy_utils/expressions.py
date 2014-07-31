import sqlalchemy as sa
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy_utils.types import TSVectorType


class tsvector_match(expression.FunctionElement):
    type = sa.types.Unicode()
    name = 'tsvector_match'


@compiles(tsvector_match)
def compile_tsvector_match(element, compiler, **kw):
    args = list(element.clauses)
    if len(args) < 2:
        raise Exception(
            "Function 'tsvector_match' expects atleast two arguments."
        )
    return '(%s) @@ %s' % (
        compiler.process(args[0]),
        compiler.process(args[1])
    )


class to_tsquery(expression.FunctionElement):
    type = sa.types.Unicode()
    name = 'to_tsquery'


@compiles(to_tsquery)
def compile_to_tsquery(element, compiler, **kw):
    if len(element.clauses) < 1:
        raise Exception(
            "Function 'to_tsquery' expects atleast one argument."
        )
    return 'to_tsquery(%s)' % (
        ', '.join(map(compiler.process, element.clauses))
    )


class plainto_tsquery(expression.FunctionElement):
    type = sa.types.Unicode()
    name = 'plainto_tsquery'


@compiles(plainto_tsquery)
def compile_plainto_tsquery(element, compiler, **kw):
    if len(element.clauses) < 1:
        raise Exception(
            "Function 'plainto_tsquery' expects atleast one argument."
        )
    return 'plainto_tsquery(%s)' % (
        ', '.join(map(compiler.process, element.clauses))
    )


class tsvector_concat(expression.FunctionElement):
    type = TSVectorType()
    name = 'tsvector_concat'


@compiles(tsvector_concat)
def compile_tsvector_concat(element, compiler, **kw):
    return ' || '.join(map(compiler.process, element.clauses))


class array_get(expression.FunctionElement):
    name = 'array_get'


@compiles(array_get)
def compile_array_get(element, compiler, **kw):
    args = list(element.clauses)
    if len(args) != 2:
        raise Exception(
            "Function 'array_get' expects two arguments (%d given)." %
            len(args)
        )

    if not hasattr(args[1], 'value') or not isinstance(args[1].value, int):
        raise Exception(
            "Second argument should be an integer."
        )
    return '(%s)[%s]' % (
        compiler.process(args[0]),
        sa.text(str(args[1].value + 1))
    )
