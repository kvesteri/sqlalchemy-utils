import sqlalchemy as sa
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement, PrimaryKeyConstraint


class CreateMaterializedView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


@compiler.compiles(CreateMaterializedView)
def compile_create_materialized_view(element, compiler, **kw):
    return 'CREATE MATERIALIZED VIEW %s AS %s' % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


class DropMateralizedView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiler.compiles(DropMateralizedView)
def compile_drop_materialized_view(element, compiler, **kw):
    return 'DROP MATERIALIZED VIEW IF EXISTS {} CASCADE'.format(
        element.name
    )


def create_table_from_selectable(
    name,
    selectable,
    indexes=None,
    metadata=None
):
    if indexes is None:
        indexes = []
    if metadata is None:
        metadata = sa.MetaData()
    args = [
        sa.Column(c.name, c.type, primary_key=c.primary_key)
        for c in selectable.c
    ] + indexes
    table = sa.Table(name, metadata, *args)

    if not any([c.primary_key for c in selectable.c]):
        table.append_constraint(
            PrimaryKeyConstraint(*[c.name for c in selectable.c])
        )
    return table


def create_materialized_view(
    name,
    selectable,
    metadata,
    indexes=None
):
    table = create_table_from_selectable(
        name=name,
        selectable=selectable,
        indexes=indexes,
        metadata=None
    )

    sa.event.listen(
        metadata,
        'after_create',
        CreateMaterializedView(name, selectable)
    )

    @sa.event.listens_for(metadata, 'after_create')
    def create_indexes(target, connection, **kw):
        for idx in table.indexes:
            idx.create(connection)

    sa.event.listen(metadata, 'before_drop', DropMateralizedView(name))
    return table


def refresh_materialized_view(session, name, concurrently=False):
    # Since session.execute() bypasses autoflush, we must manually flush in
    # order to include newly-created/modified objects in the refresh.
    session.flush()
    session.execute(
        'REFRESH MATERIALIZED VIEW {}{}'.format(
            'CONCURRENTLY ' if concurrently else '',
            name
        )
    )
