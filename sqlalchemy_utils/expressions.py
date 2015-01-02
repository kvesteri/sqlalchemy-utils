import sqlalchemy as sa
from sqlalchemy.sql import expression
from sqlalchemy.sql.expression import (
    Executable,
    ClauseElement,
    _literal_as_text
)
from sqlalchemy.ext.compiler import compiles


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
