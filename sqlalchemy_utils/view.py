import sqlalchemy as sa
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement, PrimaryKeyConstraint

from sqlalchemy_utils.functions import get_columns


class CreateView(DDLElement):
    def __init__(
        self,
        name,
        selectable,
        materialized=False,
        if_not_exists=False,
        or_replace=False,
    ):
        self.name = name
        self.selectable = selectable
        self.materialized = materialized
        self.if_not_exists = if_not_exists
        self.or_replace = or_replace


@compiler.compiles(CreateView)
def compile_create_materialized_view(element, compiler, **kw):
    return "CREATE {}{}VIEW {}{} AS {}".format(
        "OR REPLACE " if element.or_replace else "",
        "MATERIALIZED " if element.materialized else "",
        "IF NOT EXISTS " if element.if_not_exists else "",
        compiler.dialect.identifier_preparer.quote(element.name),
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


@compiler.compiles(CreateView, "postgresql")
def compile_create_materialized_view_(element, compiler, **kw):
    """
    CREATE [ OR REPLACE ] [ TEMP | TEMPORARY ] [ RECURSIVE ] VIEW name [ ( column_name [, ...] ) ]
        [ WITH ( view_option_name [= view_option_value] [, ... ] ) ]
        AS query
        [ WITH [ CASCADED | LOCAL ] CHECK OPTION ]

    CREATE MATERIALIZED VIEW [ IF NOT EXISTS ] table_name
        [ (column_name [, ...] ) ]
        [ USING method ]
        [ WITH ( storage_parameter [= value] [, ... ] ) ]
        [ TABLESPACE tablespace_name ]
        AS query
        [ WITH [ NO ] DATA ]

    see https://www.postgresql.org/docs/current/sql-createview.html
    see https://www.postgresql.org/docs/current/sql-creatematerializedview.html
    """
    return "CREATE {}{}VIEW {}{} AS {}".format(
        "OR REPLACE " if not element.materialized and element.or_replace else "",
        "MATERIALIZED " if element.materialized else "",
        "IF NOT EXISTS " if element.materialized and element.if_not_exists else "",
        compiler.dialect.identifier_preparer.quote(element.name),
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


@compiler.compiles(CreateView, "mysql")
def compile_create_materialized_view_(element, compiler, **kw):
    """
    CREATE
        [OR REPLACE]
        [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}]
        [DEFINER = user]
        [SQL SECURITY { DEFINER | INVOKER }]
        VIEW view_name [(column_list)]
        AS select_statement
        [WITH [CASCADED | LOCAL] CHECK OPTION]

    See https://dev.mysql.com/doc/refman/8.0/en/create-view.html
    NOTE mysql does not support materialized view
    """
    if element.materialized:
        raise ValueError("mysql does not support materialized view!")
    return "CREATE {}VIEW {} AS {}".format(
        "OR REPLACE " if element.or_replace else "",
        compiler.dialect.identifier_preparer.quote(element.name),
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


@compiler.compiles(CreateView, "mssql")
def compile_create_materialized_view_(element, compiler, **kw):
    """
    CREATE [ OR ALTER ] VIEW [ schema_name . ] view_name [ (column [ ,...n ] ) ]
        [ WITH <view_attribute> [ ,...n ] ]
        AS select_statement
        [ WITH CHECK OPTION ]
        [ ; ]

    CREATE MATERIALIZED VIEW [ schema_name. ] materialized_view_name
        WITH (
        <distribution_option>
        )
        AS <select_statement>
    [;]

    see https://docs.microsoft.com/en-us/sql/t-sql/statements/create-view-transact-sql?view=sql-server-ver15
    see https://docs.microsoft.com/en-us/sql/t-sql/statements/create-materialized-view-as-select-transact-sql?view=azure-sqldw-latest&viewFallbackFrom=sql-server-ver15
    """
    return "CREATE {}{}VIEW {} AS {}".format(
        "OR ALTER " if not element.materialized and element.or_replace else "",
        "MATERIALIZED " if element.materialized else "",
        compiler.dialect.identifier_preparer.quote(element.name),
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


@compiler.compiles(CreateView, "snowflake")
def compile_create_materialized_view(element, compiler, **kw):
    """
    CREATE [ OR REPLACE ] [ SECURE ] [ RECURSIVE ] VIEW [ IF NOT EXISTS ] <name>
        [ ( <column_list> ) ]
        [ <col1> [ WITH ] MASKING POLICY <policy_name> [ USING ( <col1> , <cond_col1> , ... ) ]
                [ WITH ] TAG ( <tag_name> = '<tag_value>' [ , <tag_name> = '<tag_value>' , ... ] ) ]
        [ , <col2> [ ... ] ]
        [ [ WITH ] ROW ACCESS POLICY <policy_name> ON ( <col_name> [ , <col_name> ... ] ) ]
        [ WITH ] TAG ( <tag_name> = '<tag_value>' [ , <tag_name> = '<tag_value>' , ... ] ) ]
        [ COPY GRANTS ]
        [ COMMENT = '<string_literal>' ]
        AS <select_statement>

    CREATE [ OR REPLACE ] [ SECURE ] MATERIALIZED VIEW [ IF NOT EXISTS ] <name>
        [ COPY GRANTS ]
        ( <column_list> )
        [ <col1> [ WITH ] MASKING POLICY <policy_name> [ USING ( <col1> , <cond_col1> , ... ) ]
                [ WITH ] TAG ( <tag_name> = '<tag_value>' [ , <tag_name> = '<tag_value>' , ... ] ) ]
        [ , <col2> [ ... ] ]
        [ [ WITH ] ROW ACCESS POLICY <policy_name> ON ( <col_name> [ , <col_name> ... ] ) ]
        [ WITH ] TAG ( <tag_name> = '<tag_value>' [ , <tag_name> = '<tag_value>' , ... ] ) ]
        [ COMMENT = '<string_literal>' ]
        [ CLUSTER BY ( <expr1> [, <expr2> ... ] ) ]
        AS <select_statement>

    see https://docs.snowflake.com/en/sql-reference/sql/create-view.html
    see https://docs.snowflake.com/en/sql-reference/sql/create-materialized-view.html
    """
    return "CREATE {}{}VIEW {}{} AS {}".format(
        "OR REPLACE " if element.or_replace else "",
        "MATERIALIZED " if element.materialized else "",
        "IF NOT EXISTS " if element.if_not_exists else "",
        compiler.dialect.identifier_preparer.quote(element.name),
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


class DropView(DDLElement):
    def __init__(self, name, materialized=False, cascade=True):
        self.name = name
        self.materialized = materialized
        self.cascade = cascade


@compiler.compiles(DropView)
def compile_drop_materialized_view(element, compiler, **kw):
    return "DROP {}VIEW IF EXISTS {} {}".format(
        "MATERIALIZED " if element.materialized else "",
        compiler.dialect.identifier_preparer.quote(element.name),
        "CASCADE" if element.cascade else "",
    )


def create_table_from_selectable(
    name, selectable, indexes=None, metadata=None, aliases=None, **kwargs
):
    if indexes is None:
        indexes = []
    if metadata is None:
        metadata = sa.MetaData()
    if aliases is None:
        aliases = {}
    args = [
        sa.Column(
            c.name, c.type, key=aliases.get(c.name, c.name), primary_key=c.primary_key
        )
        for c in get_columns(selectable)
    ] + indexes
    table = sa.Table(name, metadata, *args, **kwargs)

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
    if_not_exists=False,
    or_replace=False,
):
    """Create a view on a given metadata

    :param name: The name of the view to create.
    :param selectable: An SQLAlchemy selectable e.g. a select() statement.
    :param metadata:
        An SQLAlchemy Metadata instance that stores the features of the
        database being described.
    :param indexes: An optional list of SQLAlchemy Index instances.
    :param aliases:
        An optional dictionary containing with keys as column names and values
        as column aliases.
    :param if_not_exists:
        An optional flag to indicate whether to use the
        ``CREATE MATERIALIZED VIEW IF NOT EXISTS`` statement.
    :param or_replace:
        An optional flag to indicate whether to use the
        ``CREATE OR REPLACE MATERIALIZED VIEW`` statement.

    Same as for ``create_view`` except that a ``CREATE MATERIALIZED VIEW``
    statement is emitted instead of a ``CREATE VIEW``.

    """
    table = create_table_from_selectable(
        name=name,
        selectable=selectable,
        indexes=indexes,
        metadata=None,
        aliases=aliases,
    )

    sa.event.listen(
        metadata,
        "after_create",
        CreateView(
            name,
            selectable,
            materialized=True,
            if_not_exists=if_not_exists,
            or_replace=or_replace,
        ),
    )

    @sa.event.listens_for(metadata, "after_create")
    def create_indexes(target, connection, **kw):
        for idx in table.indexes:
            idx.create(connection)

    sa.event.listen(metadata, "before_drop", DropView(name, materialized=True))
    return table


def create_view(
    name,
    selectable,
    metadata,
    cascade_on_drop=True,
    if_not_exists=False,
    or_replace=False,
):
    """Create a view on a given metadata

    :param name: The name of the view to create.
    :param selectable: An SQLAlchemy selectable e.g. a select() statement.
    :param metadata:
        An SQLAlchemy Metadata instance that stores the features of the
        database being described.
    :param if_not_exists:
        An optional flag to indicate whether to use the
        ``CREATE VIEW IF NOT EXISTS`` statement.
    :param or_replace:
        An optional flag to indicate whether to use the
        ``CREATE OR REPLACE VIEW`` statement. (``OR ALTER`` will be used for mysql)

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

        premium_members = select([users]).where(users.c.premium_user == True)
        create_view('premium_users', premium_members, metadata)

        metadata.create_all(engine) # View is created at this point

    """
    table = create_table_from_selectable(
        name=name, selectable=selectable, metadata=None
    )

    sa.event.listen(
        metadata,
        "after_create",
        CreateView(
            name, selectable, if_not_exists=if_not_exists, or_replace=or_replace
        ),
    )

    @sa.event.listens_for(metadata, "after_create")
    def create_indexes(target, connection, **kw):
        for idx in table.indexes:
            idx.create(connection)

    sa.event.listen(metadata, "before_drop", DropView(name, cascade=cascade_on_drop))
    return table


def refresh_materialized_view(session, name, concurrently=False):
    """Refreshes an already existing materialized view

    :param session: An SQLAlchemy Session instance.
    :param name: The name of the materialized view to refresh.
    :param concurrently:
        Optional flag that causes the ``CONCURRENTLY`` parameter
        to be specified when the materialized view is refreshed.
    """
    # Since session.execute() bypasses autoflush, we must manually flush in
    # order to include newly-created/modified objects in the refresh.
    session.flush()
    session.execute(
        "REFRESH MATERIALIZED VIEW {}{}".format(
            "CONCURRENTLY " if concurrently else "",
            session.bind.engine.dialect.identifier_preparer.quote(name),
        )
    )
