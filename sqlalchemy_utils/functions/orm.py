try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from functools import partial
from inspect import isclass
from itertools import chain
from operator import attrgetter
import six
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapperlib
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.util import AliasedInsp


def get_column_key(model, column):
    """
    Return the key for given column in given model.

    :param model: SQLAlchemy declarative model object

    ::

        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column('_name', sa.String)


        get_column_key(User, User.__table__.c.name)  # 'name'

    .. versionadded: 0.26.5
    """
    for key, c in sa.inspect(model).columns.items():
        if c is column:
            return key
    raise ValueError(
        "Class %s doesn't have a column '%s'",
        model.__name__,
        column
    )


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
    if isinstance(mixed, sa.orm.query._MapperEntity):
        mixed = mixed.expr
    elif isinstance(mixed, sa.Column):
        mixed = mixed.table
    elif isinstance(mixed, sa.orm.query._ColumnEntity):
        mixed = mixed.expr

    if isinstance(mixed, sa.orm.Mapper):
        return mixed
    if isinstance(mixed, sa.orm.util.AliasedClass):
        return sa.inspect(mixed).mapper
    if isinstance(mixed, sa.sql.selectable.Alias):
        mixed = mixed.element
    if isinstance(mixed, AliasedInsp):
        return mixed.mapper
    if isinstance(mixed, sa.orm.attributes.InstrumentedAttribute):
        mixed = mixed.class_
    if isinstance(mixed, sa.Table):
        mappers = [
            mapper for mapper in mapperlib._mapper_registry
            if mixed in mapper.tables
        ]
        if len(mappers) > 1:
            raise ValueError(
                "Multiple mappers found for table '%s'." % mixed.name
            )
        elif not mappers:
            raise ValueError(
                "Could not get mapper for table '%s'." % mixed.name
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
    Return a set of tables associated with given SQLAlchemy object.

    Let's say we have three classes which use joined table inheritance
    TextItem, Article and BlogPost. Article and BlogPost inherit TextItem.

    ::

        get_tables(Article)  # set([Table('article', ...), Table('text_item')])

        get_tables(Article())

        get_tables(Article.__mapper__)


    If the TextItem entity is using with_polymorphic='*' then this function
    returns all child tables (article and blog_post) as well.

    ::


        get_tables(TextItem)  # set([Table('text_item', ...)], ...])


    .. versionadded: 0.26.0

    :param mixed:
        SQLAlchemy Mapper, Declarative class, Column, InstrumentedAttribute or
        a SA Alias object wrapping any of these objects.
    """
    if isinstance(mixed, sa.Table):
        return [mixed]
    elif isinstance(mixed, sa.Column):
        return [mixed.table]
    elif isinstance(mixed, sa.orm.attributes.InstrumentedAttribute):
        return mixed.parent.tables
    elif isinstance(mixed, sa.orm.query._ColumnEntity):
        mixed = mixed.expr

    mapper = get_mapper(mixed)

    polymorphic_mappers = get_polymorphic_mappers(mapper)
    if polymorphic_mappers:
        tables = sum((m.tables for m in polymorphic_mappers), [])
    else:
        tables = mapper.tables
    return tables


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


def quote(mixed, ident):
    """
    Conditionally quote an identifier.
    ::


        from sqlalchemy_utils import quote


        engine = create_engine('sqlite:///:memory:')

        quote(engine, 'order')
        # '"order"'

        quote(engine, 'some_other_identifier')
        # 'some_other_identifier'


    :param mixed: SQLAlchemy Session / Connection / Engine object.
    :param ident: identifier to conditionally quote
    """
    dialect = get_bind(mixed).dialect
    return dialect.preparer(dialect).quote(ident)


def query_labels(query):
    """
    Return all labels for given SQLAlchemy query object.

    Example::


        query = session.query(
            Category,
            db.func.count(Article.id).label('articles')
        )

        query_labels(query)  # ['articles']

    :param query: SQLAlchemy Query object
    """
    return [
        entity._label_name for entity in query._entities
        if isinstance(entity, _ColumnEntity) and entity._label_name
    ]


def get_query_entities(query):
    """
    Return a list of all entities present in given SQLAlchemy query object.

    Examples::


        from sqlalchemy_utils import get_query_entities


        query = session.query(Category)

        get_query_entities(query)  # [<Category>]


        query = session.query(Category.id)

        get_query_entities(query)  # [<Category>]


    This function also supports queries with joins.

    ::


        query = session.query(Category).join(Article)

        get_query_entities(query)  # [<Category>, <Article>]

    .. versionchanged: 0.26.7
        This function now returns a list instead of generator

    :param query: SQLAlchemy Query object
    """
    return [
        get_query_entity(entity) for entity in
        chain(query._entities, query._join_entities)
    ]


def get_query_entity(mixed):
    if hasattr(mixed, 'expr'):
        expr = mixed.expr
    else:
        expr = mixed
    if isinstance(expr, sa.orm.attributes.InstrumentedAttribute):
        return expr.parent.class_
    elif isinstance(expr, sa.Column):
        return expr.table
    elif isinstance(expr, sa.sql.expression.Label):
        if mixed.entity_zero:
            return mixed.entity_zero
        else:
            return expr
    elif isinstance(expr, sa.orm.Mapper):
        return expr.class_
    elif isinstance(expr, AliasedInsp):
        return expr.entity
    return expr


def get_query_entity_by_alias(query, alias):
    entities = get_query_entities(query)

    if not alias:
        return entities[0]

    for entity in entities:
        if isinstance(entity, sa.orm.util.AliasedClass):
            name = sa.inspect(entity).name
        else:
            name = get_mapper(entity).tables[0].name

        if name == alias:
            return entity


def get_polymorphic_mappers(mixed):
    if isinstance(mixed, AliasedInsp):
        return mixed.with_polymorphic_mappers
    else:
        return mixed.polymorphic_map.values()


def get_query_descriptor(query, entity, attr):
    if attr in query_labels(query):
        return attr
    else:
        entity = get_query_entity_by_alias(query, entity)
        if entity:
            descriptor = get_descriptor(entity, attr)
            if (
                hasattr(descriptor, 'property') and
                isinstance(descriptor.property, sa.orm.RelationshipProperty)
            ):
                return
            return descriptor


def get_descriptor(entity, attr):
    mapper = sa.inspect(entity)

    for key, descriptor in get_all_descriptors(mapper).items():
        if attr == key:
            prop = (
                descriptor.property
                if hasattr(descriptor, 'property')
                else None
            )
            if isinstance(prop, ColumnProperty):
                if isinstance(entity, sa.orm.util.AliasedClass):
                    for c in mapper.selectable.c:
                        if c.key == attr:
                            return c
                else:
                    # If the property belongs to a class that uses
                    # polymorphic inheritance we have to take into account
                    # situations where the attribute exists in child class
                    # but not in parent class.
                    return getattr(prop.parent.class_, attr)
            else:
                # Handle synonyms, relationship properties and hybrid
                # properties
                try:
                    return getattr(entity, attr)
                except AttributeError:
                    pass


def get_all_descriptors(expr):
    insp = sa.inspect(expr)
    polymorphic_mappers = get_polymorphic_mappers(insp)
    if polymorphic_mappers:
        attrs = dict(get_mapper(expr).all_orm_descriptors)
        for submapper in polymorphic_mappers:
            for key, descriptor in submapper.all_orm_descriptors.items():
                if key not in attrs:
                    attrs[key] = descriptor
        return attrs
    return get_mapper(expr).all_orm_descriptors


def get_hybrid_properties(model):
    """
    Returns a dictionary of hybrid property keys and hybrid properties for
    given SQLAlchemy declarative model / mapper.


    Consider the following model

    ::


        from sqlalchemy.ext.hybrid import hybrid_property


        class Category(Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @hybrid_property
            def lowercase_name(self):
                return self.name.lower()

            @lowercase_name.expression
            def lowercase_name(cls):
                return sa.func.lower(cls.name)


    You can now easily get a list of all hybrid property names

    ::


        from sqlalchemy_utils import get_hybrid_properties


        get_hybrid_properties(Category).keys()  # ['lowercase_name']


    .. versionchanged: 0.26.7
        This function now returns a dictionary instead of generator

    :param model: SQLAlchemy declarative model or mapper
    """
    return dict(
        (key, prop)
        for key, prop in sa.inspect(model).all_orm_descriptors.items()
        if isinstance(prop, hybrid_property)
    )


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


def has_changes(obj, attrs=None, exclude=None):
    """
    Simple shortcut function for checking if given attributes of given
    declarative model object have changed during the session. Without
    parameters this checks if given object has any modificiations. Additionally
    exclude parameter can be given to check if given object has any changes
    in any attributes other than the ones given in exclude.


    ::


        from sqlalchemy_utils import has_changes


        user = User()

        has_changes(user, 'name')  # False

        user.name = u'someone'

        has_changes(user, 'name')  # True

        has_changes(user)  # True


    You can check multiple attributes as well.
    ::


        has_changes(user, ['age'])  # True

        has_changes(user, ['name', 'age'])  # True


    This function also supports excluding certain attributes.

    ::

        has_changes(user, exclude=['name'])  # False

        has_changes(user, exclude=['age'])  # True

    .. versionchanged: 0.26.6
        Added support for multiple attributes and exclude parameter.

    :param obj: SQLAlchemy declarative model object
    :param attrs: Names of the attributes
    :param exclude: Names of the attributes to exclude
    """
    if attrs:
        if isinstance(attrs, six.string_types):
            return (
                sa.inspect(obj)
                .attrs
                .get(attrs)
                .history
                .has_changes()
            )
        else:
            return any(has_changes(obj, attr) for attr in attrs)
    else:
        if exclude is None:
            exclude = []
        return any(
            attr.history.has_changes()
            for key, attr in sa.inspect(obj).attrs.items()
            if key not in exclude
        )


def is_loaded(obj, prop):
    """
    Return whether or not given property of given object has been loaded.

    ::

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)
            content = sa.orm.deferred(sa.Column(sa.String))


        article = session.query(Article).get(5)

        # name gets loaded since its not a deferred property
        assert is_loaded(article, 'name')

        # content has not yet been loaded since its a deferred property
        assert not is_loaded(article, 'content')


    .. versionadded: 0.27.8

    :param obj: SQLAlchemy declarative model object
    :param prop: Name of the property or InstrumentedAttribute
    """
    return not isinstance(
        getattr(sa.inspect(obj).attrs, prop).loaded_value,
        sa.util.langhelpers._symbol
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
