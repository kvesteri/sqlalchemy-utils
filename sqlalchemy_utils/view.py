import sqlalchemy as sa
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement, PrimaryKeyConstraint

from sqlalchemy_utils.functions import get_columns


def _prepare_view_identifier(dialect, view_name, schema=None):
    quoted_view_name = dialect.identifier_preparer.quote(view_name)
    if schema:
        return dialect.identifier_preparer.quote_schema(schema) + '.' + quoted_view_name
    else:
        return quoted_view_name


class CreateView(DDLElement):
    def __init__(self, name, selectable, schema=None):
        self.name = name
        self.selectable = selectable
        self.schema = schema


@compiler.compiles(CreateView)
def compile_create_view(element, compiler, **kw):
    view_identifier = _prepare_view_identifier(
        compiler.dialect, element.name, element.schema
    )
    compiled_selectable = compiler.sql_compiler.process(
        element.selectable, literal_binds=True
    )
    return f'CREATE VIEW {view_identifier} AS {compiled_selectable}'


class DropView(DDLElement):
    def __init__(self, name, schema=None, cascade=None):
        self.name = name
        self.schema = schema
        self.cascade = cascade


@compiler.compiles(DropView)
def compile_drop_view(element, compiler, **kw):
    view_identifier = _prepare_view_identifier(
        compiler.dialect, element.name, element.schema
    )

    stmt = f'DROP VIEW IF EXISTS {view_identifier}'
    if element.cascade is True:
        stmt += ' CASCADE'
    elif element.cascade is False:
        stmt += ' RESTRICT'
    return stmt


class CreateMaterializedView(DDLElement):
    def __init__(self, name, selectable, schema=None, populate=None):
        self.name = name
        self.selectable = selectable
        self.schema = schema
        self.populate = populate


@compiler.compiles(CreateMaterializedView)
def compile_create_materialized_view(element, compiler, **kw):
    view_identifier = _prepare_view_identifier(
        dialect=compiler.dialect, view_name=element.name, schema=element.schema
    )
    compiled_selectable = compiler.sql_compiler.process(
        element.selectable, literal_binds=True
    )

    stmt = f'CREATE MATERIALIZED VIEW {view_identifier} AS {compiled_selectable}'
    if element.populate is True:
        stmt += ' WITH DATA'
    elif element.populate is False:
        stmt += ' WITH NO DATA'
    return stmt


class DropMaterializedView(DDLElement):
    def __init__(self, name, schema=None, cascade=None):
        self.name = name
        self.schema = schema
        self.cascade = cascade


@compiler.compiles(DropMaterializedView)
def compile_drop_materialized_view(element, compiler, **kw):
    view_identifier = _prepare_view_identifier(
        dialect=compiler.dialect, view_name=element.name, schema=element.schema
    )
    stmt = f'DROP MATERIALIZED VIEW IF EXISTS {view_identifier}'
    if element.cascade is True:
        stmt += ' CASCADE'
    elif element.cascade is False:
        stmt += ' RESTRICT'
    return stmt


def create_table_from_selectable(
    name,
    selectable,
    indexes=None,
    metadata=None,
    aliases=None,
    schema=None,
    **kwargs
):
    if indexes is None:
        indexes = []
    if metadata is None:
        metadata = sa.MetaData()
    if aliases is None:
        aliases = {}
    args = [
        sa.Column(
            c.name,
            c.type,
            key=aliases.get(c.name, c.name),
            primary_key=c.primary_key
        )
        for c in get_columns(selectable)
    ] + indexes
    table = sa.Table(name, metadata, *args, schema=schema, **kwargs)

    if not any([c.primary_key for c in get_columns(selectable)]):
        table.append_constraint(
            PrimaryKeyConstraint(*[c.name for c in get_columns(selectable)])
        )
    return table


def create_materialized_view(
    name,
    selectable,
    metadata,
    indexes=None,
    aliases=None,
    *,
    schema=None,
    populate=None,
    cascade_on_drop=None,
):
    """ Create a view on a given metadata

    :param name: The name of the view to create.
    :param selectable: An SQLAlchemy selectable e.g. a select() statement.
    :param metadata:
        An SQLAlchemy Metadata instance that stores the features of the
        database being described.
    :param indexes: An optional list of SQLAlchemy Index instances.
    :param aliases:
        An optional dictionary containing with keys as column names and values
        as column aliases.
    :param schema: The name of the schema where the view will be created (optional).
    :param populate:
        Set ``populate=True`` to create the view with ``WITH DATA``.
        Set ``populate=False`` to create the view with ``WITH NO DATA``.
        Default to ``None`` for no flags.
        See also: https://www.postgresql.org/docs/current/sql-createview.html
    :param cascade_on_drop:
        Set ``cascade_on_drop=True`` to drop the view with ``CASCADE``.
        Set ``cascade_on_drop=False`` to create the view with ``RESTRICT``.
        Default to ``None`` for no flags.
        See also: https://www.postgresql.org/docs/current/sql-dropmaterializedview.html

    Same as for ``create_view`` except that a ``CREATE MATERIALIZED VIEW``
    statement is emitted instead of a ``CREATE VIEW``.

    """
    table = create_table_from_selectable(
        name=name,
        selectable=selectable,
        indexes=indexes,
        metadata=None,
        aliases=aliases,
        schema=schema,
    )

    sa.event.listen(
        metadata,
        'after_create',
        CreateMaterializedView(name, selectable, schema=schema, populate=populate)
    )

    @sa.event.listens_for(metadata, 'after_create')
    def create_indexes(target, connection, **kw):
        for idx in table.indexes:
            idx.create(connection)

    sa.event.listen(
        metadata,
        'before_drop',
        DropMaterializedView(name, schema=schema, cascade=cascade_on_drop)
    )
    return table


def create_view(
    name,
    selectable,
    metadata,
    *,
    schema=None,
    cascade_on_drop=None,
):
    """ Create a view on a given metadata

    :param name: The name of the view to create.
    :param selectable: An SQLAlchemy selectable e.g. a select() statement.
    :param metadata:
        An SQLAlchemy Metadata instance that stores the features of the
        database being described.
    :param schema: The name of the schema where the view will be created (optional).
    :param cascade_on_drop:
        Set ``cascade_on_drop=True`` to drop the view with ``CASCADE``.
        Set ``cascade_on_drop=False`` to create the view with ``RESTRICT``.
        Default to ``None`` for no flags.

    The process for creating a view is similar to the standard way that a
    table is constructed, except that a selectable is provided instead of
    a set of columns. The view is created once a ``CREATE`` statement is
    executed against the supplied metadata (e.g. ``metadata.create_all(..)``),
    and dropped when a ``DROP`` is executed against the metadata.

    To create a view that performs basic filtering on a table. ::

        metadata = MetaData()
        users = Table('users', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String),
                Column('fullname', String),
                Column('premium_user', Boolean, default=False),
            )

        premium_members = select(users).where(users.c.premium_user == True)
        # sqlalchemy 1.3:
        # premium_members = select([users]).where(users.c.premium_user == True)
        create_view('premium_users', premium_members, metadata)

        metadata.create_all(engine) # View is created at this point

    """
    table = create_table_from_selectable(
        name=name,
        selectable=selectable,
        metadata=None,
        schema=schema,
    )

    sa.event.listen(
        metadata,
        'after_create',
        CreateView(name, selectable, schema=schema),
    )

    @sa.event.listens_for(metadata, 'after_create')
    def create_indexes(target, connection, **kw):
        for idx in table.indexes:
            idx.create(connection)

    sa.event.listen(
        metadata,
        'before_drop',
        DropView(name, schema=schema, cascade=cascade_on_drop)
    )
    return table


def refresh_materialized_view(session, name, concurrently=False, *, schema=None):
    """ Refreshes an already existing materialized view

    :param session: An SQLAlchemy Session instance.
    :param name: The name of the materialized view to refresh.
    :param concurrently:
        Optional flag that causes the ``CONCURRENTLY`` parameter
        to be specified when the materialized view is refreshed.
    :param schema: The schema of the view to be refreshed (optional).
    """
    # Since session.execute() bypasses autoflush, we must manually flush in
    # order to include newly-created/modified objects in the refresh.
    session.flush()
    session.execute(
        sa.text('REFRESH MATERIALIZED VIEW {}{}'.format(
            'CONCURRENTLY ' if concurrently else '',
            _prepare_view_identifier(session.bind.engine.dialect, name, schema),
        ))
    )
