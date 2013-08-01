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
    if len(args) == 2:
        return '(%s) @@ to_tsquery(%s)' % (
            compiler.process(args[0]),
            compiler.process(args[1])
        )
    elif len(args) == 3:
        return '(%s) @@ to_tsquery(%s, %s)' % (
            compiler.process(args[0]),
            compiler.process(args[2]),
            compiler.process(args[1])
        )


class tsvector_concat(expression.FunctionElement):
    type = TSVectorType()
    name = 'tsvector_concat'


@compiles(tsvector_concat)
def compile_tsvector_concat(element, compiler, **kw):
    return ' || '.join(map(compiler.process, element.clauses))
