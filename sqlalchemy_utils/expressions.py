import sqlalchemy as sa
from sqlalchemy.sql import expression
from sqlalchemy.sql.expression import (
    Executable,
    ClauseElement,
    _literal_as_text
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy_utils.types import TSVectorType


class explain(Executable, ClauseElement):
    """
    Define EXPLAIN element.

    http://www.postgresql.org/docs/devel/static/sql-explain.html
    """
    def __init__(
        self,
        stmt,
        analyze=False,
        verbose=False,
        costs=True,
        buffers=False,
        timing=True,
        format='text'
    ):
        self.statement = _literal_as_text(stmt)
        self.analyze = analyze
        self.verbose = verbose
        self.costs = costs
        self.buffers = buffers
        self.timing = timing
        self.format = format


class explain_analyze(explain):
    def __init__(self, stmt, **kwargs):
        super(explain_analyze, self).__init__(
            stmt,
            analyze=True,
            **kwargs
        )


@compiles(explain, 'postgresql')
def pg_explain(element, compiler, **kw):
    text = "EXPLAIN "
    options = []
    if element.analyze:
        options.append('ANALYZE true')
    if not element.timing:
        options.append('TIMING false')
    if element.buffers:
        options.append('BUFFERS true')
    if element.format != 'text':
        options.append('FORMAT %s' % element.format)
    if element.verbose:
        options.append('VERBOSE true')
    if not element.costs:
        options.append('COSTS false')
    if options:
        text += '(%s) ' % ', '.join(options)
    text += compiler.process(element.statement)
    return text


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
