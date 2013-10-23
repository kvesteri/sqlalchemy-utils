from collections import defaultdict
import six
import re
import datetime
import contextlib
import inspect
import sqlalchemy as sa
from sqlalchemy.orm.query import Query
from sqlalchemy.schema import MetaData, Table, ForeignKeyConstraint
from six.moves import cStringIO
from .batch_fetch import batch_fetch, with_backrefs, CompositePath
from .defer_except import defer_except
from .sort_query import sort_query, QuerySorterException


__all__ = (
    batch_fetch,
    defer_except,
    sort_query,
    with_backrefs,
    CompositePath,
    QuerySorterException
)


def escape_like(string, escape_char='*'):
    """
    Escapes the string paremeter used in SQL LIKE expressions

        >>> from sqlalchemy_utils import escape_like
        >>> query = session.query(User).filter(
        ...     User.name.ilike(escape_like('John'))
        ... )


    :param string: a string to escape
    :param escape_char: escape character
    """
    return (
        string
        .replace(escape_char, escape_char * 2)
        .replace('%', escape_char + '%')
        .replace('_', escape_char + '_')
    )


def remove_property(class_, name):
    """
    **Experimental function**

    Remove property from declarative class
    """
    mapper = class_.mapper
    table = class_.__table__
    columns = class_.mapper.c
    column = columns[name]
    del columns._data[name]
    del mapper.columns[name]
    columns._all_cols.remove(column)
    mapper._cols_by_table[table].remove(column)
    mapper.class_manager.uninstrument_attribute(name)
    del mapper._props[name]


def primary_keys(class_):
    """
    Returns all primary keys for given declarative class.
    """
    for column in class_.__table__.c:
        if column.primary_key:
            yield column


def table_name(obj):
    """
    Return table name of given target, declarative class or the
    table name where the declarative attribute is bound to.
    """
    class_ = getattr(obj, 'class_', obj)

    try:
        return class_.__tablename__
    except AttributeError:
        pass

    try:
        return class_.__table__.name
    except AttributeError:
        pass


def non_indexed_foreign_keys(metadata, engine=None):
    """
    Finds all non indexed foreign keys from all tables of given MetaData.

    Very useful for optimizing postgresql database and finding out which
    foreign keys need indexes.

    :param metadata: MetaData object to inspect tables from
    """
    reflected_metadata = MetaData()

    if metadata.bind is None and engine is None:
        raise Exception(
            'Either pass a metadata object with bind or '
            'pass engine as a second parameter'
        )

    constraints = defaultdict(list)

    for table_name in metadata.tables.keys():
        table = Table(
            table_name,
            reflected_metadata,
            autoload=True,
            autoload_with=metadata.bind or engine
        )

        for constraint in table.constraints:
            if not isinstance(constraint, ForeignKeyConstraint):
                continue

            if not is_indexed_foreign_key(constraint):
                constraints[table.name].append(constraint)

    return dict(constraints)


def is_indexed_foreign_key(constraint):
    """
    Whether or not given foreign key constraint's columns have been indexed.

    :param constraint: ForeignKeyConstraint object to check the indexes
    """
    for index in constraint.table.indexes:
        index_column_names = set([
            column.name for column in index.columns
        ])
        if index_column_names == set(constraint.columns):
            return True
    return False


def declarative_base(model):
    """
    Returns the declarative base for given model class.

    :param model: SQLAlchemy declarative model
    """
    for parent in model.__bases__:
        try:
            parent.metadata
            return declarative_base(parent)
        except AttributeError:
            pass
    return model


def is_auto_assigned_date_column(column):
    """
    Returns whether or not given SQLAlchemy Column object's is auto assigned
    DateTime or Date.

    :param column: SQLAlchemy Column object
    """
    return (
        (
            isinstance(column.type, sa.DateTime) or
            isinstance(column.type, sa.Date)
        )
        and
        (
            column.default or
            column.server_default or
            column.onupdate or
            column.server_onupdate
        )
    )


def has_changes(obj, attr):
    """
    Simple shortcut function for checking if given attribute of given
    declarative model object has changed during the transaction.

    :param obj: SQLAlchemy declarative model object
    :param attr: Name of the attribute
    """
    return (
        sa.inspect(obj)
        .attrs
        .get(attr)
        .history
        .has_changes()
    )


def identity(obj):
    """
    Return the identity of given sqlalchemy declarative model instance as a
    tuple. This differs from obj._sa_instance_state.identity in a way that it
    always returns the identity even if object is still in transient state (
    new object that is not yet persisted into database).

    :param obj: SQLAlchemy declarative model object
    """
    id_ = []
    for attr in obj._sa_class_manager.values():
        prop = attr.property
        if isinstance(prop, sa.orm.ColumnProperty):
            column = prop.columns[0]
            if column.primary_key:
                id_.append(getattr(obj, column.name))
    return tuple(id_)


def naturally_equivalent(obj, obj2):
    """
    Returns whether or not two given SQLAlchemy declarative instances are
    naturally equivalent (all their non primary key properties are equivalent).

    :param obj: SQLAlchemy declarative model object
    :param obj2: SQLAlchemy declarative model object to compare with `obj`
    """
    for prop in sa.inspect(obj.__class__).iterate_properties:
        if not isinstance(prop, sa.orm.ColumnProperty):
            continue

        if prop.columns[0].primary_key:
            continue

        if not (getattr(obj, prop.key) == getattr(obj2, prop.key)):
            return False
    return True


def create_mock_engine(bind, stream=None):
    """Create a mock SQLAlchemy engine from the passed engine or bind URL.

    :param bind: A SQLAlchemy engine or bind URL to mock.
    :param stream: Render all DDL operations to the stream.
    """

    if not isinstance(bind, six.string_types):
        bind_url = str(bind.url)

    else:
        bind_url = bind

    if stream is not None:

        def dump(sql, *args, **kwargs):

            class Compiler(type(sql._compiler(engine.dialect))):

                def visit_bindparam(self, bindparam, *args, **kwargs):
                    return self.render_literal_value(
                        bindparam.value, bindparam.type)

                def render_literal_value(self, value, type_):
                    if isinstance(value, six.integer_types):
                        return str(value)

                    elif isinstance(value, (datetime.date, datetime.datetime)):
                        return "'%s'" % value

                    return super(Compiler, self).render_literal_value(
                        value, type_)

            text = str(Compiler(engine.dialect, sql).process(sql))
            text = re.sub(r'\n+', '\n', text)
            text = text.strip('\n').strip()

            stream.write('\n')
            stream.write(text)
            stream.write(';')

    else:

        dump = lambda *a, **kw: None

    engine = sa.create_engine(bind_url, strategy='mock', executor=dump)
    return engine


@contextlib.contextmanager
def mock_engine(engine, stream=None):
    """Mocks out the engine specified in the passed bind expression.

    Note this function is meant for convenience and protected usage. Do NOT
    blindly pass user input to this function as it uses exec.

    :param engine: A python expression that represents the engine to mock.
    :param stream: Render all DDL operations to the stream.
    """

    # Create a stream if not present.

    if stream is None:
        stream = cStringIO()

    # Navigate the stack and find the calling frame that allows the
    # expression to execuate.

    for frame in inspect.stack()[1:]:

        try:
            frame = frame[0]
            expression = '__target = %s' % engine
            six.exec_(expression, frame.f_globals, frame.f_locals)
            target = frame.f_locals['__target']
            break

        except:
            pass

    else:

        raise ValueError('Not a valid python expression', engine)

    # Evaluate the expression and get the target engine.

    frame.f_locals['__mock'] = create_mock_engine(target, stream)

    # Replace the target with our mock.

    six.exec_('%s = __mock' % engine, frame.f_globals, frame.f_locals)

    # Give control back.

    yield stream

    # Put the target engine back.

    frame.f_locals['__target'] = target
    six.exec_('%s = __target' % engine, frame.f_globals, frame.f_locals)
    six.exec_('del __target', frame.f_globals, frame.f_locals)
    six.exec_('del __mock', frame.f_globals, frame.f_locals)


def render_expression(expression, bind, stream=None):
    """Generate a SQL expression from the passed python expression.

    Only the global variable, `engine`, is available for use in the
    expression. Additional local variables may be passed in the context
    parameter.

    Note this function is meant for convenience and protected usage. Do NOT
    blindly pass user input to this function as it uses exec.

    :param bind: A SQLAlchemy engine or bind URL.
    :param stream: Render all DDL operations to the stream.
    """

    # Create a stream if not present.

    if stream is None:
        stream = cStringIO()

    engine = create_mock_engine(bind, stream)

    # Navigate the stack and find the calling frame that allows the
    # expression to execuate.

    for frame in inspect.stack()[1:]:

        try:
            frame = frame[0]
            local = dict(frame.f_locals)
            local['engine'] = engine
            six.exec_(expression, frame.f_globals, local)
            break

        except:
            pass

    else:

        raise ValueError('Not a valid python expression', engine)

    return stream


def render_statement(statement, bind=None):
    """
    Generate an SQL expression string with bound parameters rendered inline
    for the given SQLAlchemy statement.

    :param statement: SQLAlchemy Query object.
    :param bind:
        Optional SQLAlchemy bind, if None uses the bind of the given query
        object.
    """

    if isinstance(statement, Query):
        if bind is None:
            bind = statement.session.get_bind(statement._mapper_zero_or_none())

        statement = statement.statement

    elif bind is None:
        bind = statement.bind

    stream = cStringIO()
    engine = create_mock_engine(bind.engine, stream=stream)
    engine.execute(statement)

    return stream.getvalue()
