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


def force_auto_coercion(mapper=None):
    """
    Function that assigns automatic data type coercion for all classes which
    are of type of given mapper. The coercion is applied to all coercion
    capable properties. By default coercion is applied to all SQLAlchemy
    mappers.

    Before initializing your models you need to call force_auto_coercion.

    ::

        from sqlalchemy_utils import force_auto_coercion


        force_auto_coercion()


    Then define your models the usual way::


        class Document(Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(50))
            background_color = sa.Column(ColorType)


    Now scalar values for coercion capable data types will convert to
    appropriate value objects::

        document = Document()
        document.background_color = 'F5F5F5'
        document.background_color  # Color object
        session.commit()


    :param mapper: The mapper which the automatic data type coercion should be
                   applied to
    """
    if mapper is None:
        mapper = sa.orm.mapper
    sa.event.listen(mapper, 'mapper_configured', coercion_listener)


def force_instant_defaults(mapper=None):
    """
    Function that assigns object column defaults on object initialization
    time. By default calling this function applies instant defaults to all
    your models.

    Setting up instant defaults::


        from sqlalchemy_utils import force_instant_defaults


        force_instant_defaults()

    Example usage::


        class Document(Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(50))
            created_at = sa.Column(sa.DateTime, default=datetime.now)


        document = Document()
        document.created_at  # datetime object


    :param mapper: The mapper which the automatic instant defaults forcing
                   should be applied to
    """
    if mapper is None:
        mapper = sa.orm.mapper
    sa.event.listen(mapper, 'init', instant_defaults_listener)
