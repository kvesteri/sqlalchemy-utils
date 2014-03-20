from functools import partial
from operator import attrgetter
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.util import AliasedInsp


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


    This function also supports queries with joins:


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


def attrs(expr):
    if isinstance(expr, AliasedInsp):
        return expr.mapper.attrs
    else:
        return inspect(expr).attrs


def get_expr_attr(expr, attr_name):
    if isinstance(expr, AliasedInsp):
        return getattr(expr.selectable.c, attr_name)
    else:
        return getattr(expr, attr_name)


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
        getattr(obj_or_class, column.name)
        for column in primary_keys(obj_or_class)
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
