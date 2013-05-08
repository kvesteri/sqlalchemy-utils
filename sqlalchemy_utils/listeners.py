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
