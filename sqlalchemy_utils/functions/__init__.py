from collections import defaultdict
import six
import datetime
import sqlalchemy as sa
from sqlalchemy.orm import defer
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.query import Query
from sqlalchemy.schema import MetaData, Table, ForeignKeyConstraint
from .batch_fetch import batch_fetch, with_backrefs, CompositePath
from .sort_query import sort_query


__all__ = (
    batch_fetch,
    sort_query,
    with_backrefs,
    CompositePath,
)


def defer_except(query, columns):
    """
    Deferred loads all columns in given query, except the ones given.

    This function is very useful when working with models with myriad of
    columns and you want to deferred load many columns.

        >>> from sqlalchemy_utils import defer_except
        >>> query = session.query(Article)
        >>> query = defer_except(Article, [Article.id, Article.name])

    :param columns: columns not to deferred load
    """
    model = query._entities[0].entity_zero.class_
    fields = set(model._sa_class_manager.values())
    for field in fields:
        property_ = field.property
        if isinstance(property_, ColumnProperty):
            column = property_.columns[0]
            if column.name not in columns:
                query = query.options(defer(property_.key))
    return query


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


def render_statement(statement, bind=None):
    """
    Generate an SQL expression string with bound parameters rendered inline
    for the given SQLAlchemy statement.
    """

    if isinstance(statement, Query):
        if bind is None:
            bind = statement.session.get_bind(statement._mapper_zero_or_none())

        statement = statement.statement

    elif bind is None:
        bind = statement.bind

    class Compiler(bind.dialect.statement_compiler):

        def visit_bindparam(self, bindparam, *args, **kwargs):
            return self.render_literal_value(bindparam.value, bindparam.type)

        def render_literal_value(self, value, type_):
            if isinstance(value, six.integer_types):
                return str(value)

            elif isinstance(value, (datetime.date, datetime.datetime)):
                return "'%s'" % value

            return super(Compiler, self).render_literal_value(value, type_)

    return Compiler(bind.dialect, statement).process(statement)
