import sqlalchemy as sa


def coercion_listener(mapper, class_):
    """
    Auto assigns coercing listener for all class properties which are of coerce
    capable type.
    """
    for prop in mapper.iterate_properties:
        try:
            listener = prop.columns[0].type.coercion_listener
        except AttributeError:
            continue
        sa.event.listen(
            getattr(class_, prop.key),
            'set',
            listener,
            retval=True
        )


def instant_defaults_listener(target, args, kwargs):
    for key, column in sa.inspect(target.__class__).columns.items():
        if column.default is not None:
            if callable(column.default.arg):
                setattr(target, key, column.default.arg(target))
            else:
                setattr(target, key, column.default.arg)


def coerce_data_types(mapper=sa.orm.mapper):
    sa.event.listen(mapper, 'mapper_configured', coercion_listener)


def force_instant_defaults(mapper=sa.orm.mapper):
    sa.event.listen(mapper, 'init', instant_defaults_listener)
