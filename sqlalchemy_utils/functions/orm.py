try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from functools import partial
from inspect import isclass
from operator import attrgetter
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapperlib
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.util import AliasedInsp


def get_mapper(mixed):
    """
    Return related SQLAlchemy Mapper for given SQLAlchemy object.

    :param mixed: SQLAlchemy Table / Alias / Mapper / declarative model object

    ::

        from sqlalchemy_utils import get_mapper


        get_mapper(User)

        get_mapper(User())

        get_mapper(User.__table__)

        get_mapper(User.__mapper__)

        get_mapper(sa.orm.aliased(User))

        get_mapper(sa.orm.aliased(User.__table__))


    Raises:
        ValueError: if multiple mappers were found for given argument

    .. versionadded: 0.26.1
    """
    if isinstance(mixed, sa.orm.Mapper):
        return mixed
    if isinstance(mixed, sa.orm.util.AliasedClass):
        return sa.inspect(mixed).mapper
    if isinstance(mixed, sa.sql.selectable.Alias):
        mixed = mixed.element
    if isinstance(mixed, sa.Table):
        mappers = [
            mapper for mapper in mapperlib._mapper_registry
            if mixed in mapper.tables
        ]
        if len(mappers) > 1:
            raise ValueError(
                "Multiple mappers found for table '%s'."
                % mixed.name
            )
        elif not mappers:
            raise ValueError(
                "Could not get mapper for table '%s'."
            )
        else:
            return mappers[0]
    if not isclass(mixed):
        mixed = type(mixed)
    return sa.inspect(mixed)


def get_bind(obj):
    """
    Return the bind for given SQLAlchemy Engine / Connection / declarative
    model object.

    :param obj: SQLAlchemy Engine / Connection / declarative model object

    ::

        from sqlalchemy_utils import get_bind


        get_bind(session)  # Connection object

        get_bind(user)

    """
    if hasattr(obj, 'bind'):
        conn = obj.bind
    else:
        try:
            conn = object_session(obj).bind
        except UnmappedInstanceError:
            conn = obj

    if not hasattr(conn, 'execute'):
        raise TypeError(
            'This method accepts only Session, Engine, Connection and '
            'declarative model objects.'
        )
    return conn


def get_primary_keys(mixed):
    """
    Return an OrderedDict of all primary keys for given Table object,
    declarative class or declarative class instance.

    :param mixed:
        SA Table object, SA declarative class or SA declarative class instance

    ::

        get_primary_keys(User)

        get_primary_keys(User())

        get_primary_keys(User.__table__)

        get_primary_keys(User.__mapper__)

        get_primary_keys(sa.orm.aliased(User))

        get_primary_keys(sa.orm.aliased(User.__table__))


    .. versionchanged: 0.25.3
        Made the function return an ordered dictionary instead of generator.
        This change was made to support primary key aliases.

        Renamed this function to 'get_primary_keys', formerly 'primary_keys'

    .. seealso:: :func:`get_columns`
    """
    return OrderedDict(
        (
            (key, column) for key, column in get_columns(mixed).items()
            if column.primary_key
        )
    )


def get_tables(mixed):
    """
    Return a list of tables associated with given SQLAlchemy object.

    Let's say we have three classes which use joined table inheritance
    TextItem, Article and BlogPost. Article and BlogPost inherit TextItem.

    ::

        get_tables(Article)  # [Table('article', ...), Table('text_item')]

        get_tables(Article())

        get_tables(Article.__mapper__)


    .. versionadded: 0.26.0

    :param mixed:
        SQLAlchemy Mapper / Declarative class or a SA Alias object wrapping
        any of these objects.
    """
    if isinstance(mixed, sa.orm.util.AliasedClass):
        mapper = sa.inspect(mixed).mapper
    else:
        if not isclass(mixed):
            mixed = mixed.__class__
        mapper = sa.inspect(mixed)
    return mapper.tables


def get_columns(mixed):
    """
    Return a collection of all Column objects for given SQLAlchemy
    object.

    The type of the collection depends on the type of the object to return the
    columns from.

    ::

        get_columns(User)

        get_columns(User())

        get_columns(User.__table__)

        get_columns(User.__mapper__)

        get_columns(sa.orm.aliased(User))

        get_columns(sa.orm.alised(User.__table__))


    :param mixed:
        SA Table object, SA Mapper, SA declarative class, SA declarative class
        instance or an alias of any of these objects
    """
    if isinstance(mixed, sa.Table):
        return mixed.c
    if isinstance(mixed, sa.orm.util.AliasedClass):
        return sa.inspect(mixed).mapper.columns
    if isinstance(mixed, sa.sql.selectable.Alias):
        return mixed.c
    if isinstance(mixed, sa.orm.Mapper):
        return mixed.columns
    if not isclass(mixed):
        mixed = mixed.__class__
    return sa.inspect(mixed).columns


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


def getattrs(obj, attrs):
    return map(partial(getattr, obj), attrs)


def local_values(prop, entity):
    return tuple(getattrs(entity, local_column_names(prop)))


def list_local_values(prop, entities):
    return map(partial(local_values, prop), entities)


def remote_values(prop, entity):
    return tuple(getattrs(entity, remote_column_names(prop)))


def local_remote_expr(prop, entity):
    return sa.and_(
        *[
            getattr(remote(prop), r.name)
            ==
            getattr(entity, l.name)
            for l, r in prop.local_remote_pairs
            if r in remote_column_names(prop)
        ]
    )


def list_local_remote_exprs(prop, entities):
    return map(partial(local_remote_expr, prop), entities)


def remote(prop):
    try:
        return prop.secondary.c
    except AttributeError:
        return prop.mapper.class_


def local_column_names(prop):
    if not hasattr(prop, 'secondary'):
        yield prop._discriminator_col.key
        for id_col in prop._id_cols:
            yield id_col.key
    elif prop.secondary is None:
        for local, _ in prop.local_remote_pairs:
            yield local.name
    else:
        if prop.secondary is not None:
            for local, remote in prop.local_remote_pairs:
                for fk in remote.foreign_keys:
                    if fk.column.table in prop.parent.tables:
                        yield local.name


def remote_column_names(prop):
    if not hasattr(prop, 'secondary'):
        yield '__tablename__'
        yield 'id'
    elif prop.secondary is None:
        for _, remote in prop.local_remote_pairs:
            yield remote.name
    else:
        for _, remote in prop.local_remote_pairs:
            for fk in remote.foreign_keys:
                if fk.column.table in prop.parent.tables:
                    yield remote.name


def query_labels(query):
    """
    Return all labels for given SQLAlchemy query object.

    Example::


        query = session.query(
            Category,
            db.func.count(Article.id).label('articles')
        )

        query_labels(query)  # ('articles', )

    :param query: SQLAlchemy Query object
    """
    for entity in query._entities:
        if isinstance(entity, _ColumnEntity) and entity._label_name:
            yield entity._label_name


def query_entities(query):
    """
    Return a generator that iterates through all entities for given SQLAlchemy
    query object.

    Examples::


        query = session.query(Category)

        query_entities(query)  # <Category>


        query = session.query(Category.id)

        query_entities(query)  # <Category>


    This function also supports queries with joins.

    ::


        query = session.query(Category).join(Article)

        query_entities(query)  # (<Category>, <Article>)


    :param query: SQLAlchemy Query object
    """
    for entity in query._entities:
        if entity.entity_zero:
            yield entity.entity_zero.class_

    for entity in query._join_entities:
        if isinstance(entity, Mapper):
            yield entity.class_
        else:
            yield entity


def get_query_entity_by_alias(query, alias):
    entities = query_entities(query)
    if not alias:
        return list(entities)[0]

    for entity in entities:
        if isinstance(entity, AliasedInsp):
            name = entity.name
        else:
            name = entity.__table__.name

        if name == alias:
            return entity


def get_attrs(expr):
    if isinstance(expr, AliasedInsp):
        return expr.mapper.attrs
    else:
        return inspect(expr).attrs


def get_hybrid_properties(class_):
    for prop in sa.inspect(class_).all_orm_descriptors:
        if isinstance(prop, hybrid_property):
            yield prop


def get_expr_attr(expr, attr_name):
    if isinstance(expr, AliasedInsp):
        return getattr(expr.selectable.c, attr_name)
    else:
        return getattr(expr, attr_name)


def get_declarative_base(model):
    """
    Returns the declarative base for given model class.

    :param model: SQLAlchemy declarative model
    """
    for parent in model.__bases__:
        try:
            parent.metadata
            return get_declarative_base(parent)
        except AttributeError:
            pass
    return model


def getdotattr(obj_or_class, dot_path):
    """
    Allow dot-notated strings to be passed to `getattr`.

    ::

        getdotattr(SubSection, 'section.document')

        getdotattr(subsection, 'section.document')


    :param obj_or_class: Any object or class
    :param dot_path: Attribute path with dot mark as separator
    """
    last = obj_or_class
    # Coerce object style paths to strings.
    path = str(dot_path)

    for path in dot_path.split('.'):
        getter = attrgetter(path)
        if isinstance(last, list):
            tmp = []
            for el in last:
                if isinstance(el, list):
                    tmp.extend(map(getter, el))
                else:
                    tmp.append(getter(el))
            last = tmp
        elif isinstance(last, InstrumentedAttribute):
            last = getter(last.property.mapper.class_)
        elif last is None:
            return None
        else:
            last = getter(last)
    return last


def has_changes(obj, attr):
    """
    Simple shortcut function for checking if given attribute of given
    declarative model object has changed during the transaction.


    ::


        from sqlalchemy_utils import has_changes


        user = User()

        has_changes(user, 'name')  # False

        user.name = u'someone'

        has_changes(user, 'name')  # True


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


def identity(obj_or_class):
    """
    Return the identity of given sqlalchemy declarative model class or instance
    as a tuple. This differs from obj._sa_instance_state.identity in a way that
    it always returns the identity even if object is still in transient state (
    new object that is not yet persisted into database). Also for classes it
    returns the identity attributes.

    ::

        from sqlalchemy import inspect
        from sqlalchemy_utils import identity


        user = User(name=u'John Matrix')
        session.add(user)
        identity(user)  # None
        inspect(user).identity  # None

        session.flush()  # User now has id but is still in transient state

        identity(user)  # (1,)
        inspect(user).identity  # None

        session.commit()

        identity(user)  # (1,)
        inspect(user).identity  # (1, )


    You can also use identity for classes::


        identity(User)  # (User.id, )

    .. versionadded: 0.21.0

    :param obj: SQLAlchemy declarative model object
    """
    return tuple(
        getattr(obj_or_class, column_key)
        for column_key in get_primary_keys(obj_or_class).keys()
    )


def naturally_equivalent(obj, obj2):
    """
    Returns whether or not two given SQLAlchemy declarative instances are
    naturally equivalent (all their non primary key properties are equivalent).


    ::

        from sqlalchemy_utils import naturally_equivalent


        user = User(name=u'someone')
        user2 = User(name=u'someone')

        user == user2  # False

        naturally_equivalent(user, user2)  # True


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
