from collections import defaultdict
import six
import datetime
import sqlalchemy as sa
from sqlalchemy.orm import defer, RelationshipProperty
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.query import _ColumnEntity, Query
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.util import AliasedInsp
from sqlalchemy.schema import MetaData, Table, ForeignKeyConstraint
from sqlalchemy.sql.expression import desc, asc, Label


class QuerySorter(object):
    def __init__(self, separator='-'):
        self.entities = []
        self.labels = []
        self.separator = separator

    def inspect_labels_and_entities(self):
        for entity in self.query._entities:
            # get all label names for queries such as:
            # db.session.query(
            #       Category,
            #       db.func.count(Article.id).label('articles')
            # )
            if isinstance(entity, _ColumnEntity) and entity._label_name:
                self.labels.append(entity._label_name)
            else:
                self.entities.append(entity.entity_zero.class_)

        for mapper in self.query._join_entities:
            if isinstance(mapper, Mapper):
                self.entities.append(mapper.class_)
            else:
                self.entities.append(mapper)

    def assign_order_by(self, sort):
        if not sort:
            return self.query

        sort = self.parse_sort_arg(sort)
        if sort['attr'] in self.labels:
            return self.query.order_by(sort['func'](sort['attr']))

        for entity in self.entities:
            if isinstance(entity, AliasedInsp):
                if sort['entity'] and entity.name != sort['entity']:
                    continue

                selectable = entity.selectable

                if sort['attr'] in selectable.c:
                    attr = selectable.c[sort['attr']]
                    return self.query.order_by(sort['func'](attr))
            else:
                table = entity.__table__
                if sort['entity'] and table.name != sort['entity']:
                    continue
                return self.assign_entity_attr_order_by(entity, sort)
        return self.query

    def assign_entity_attr_order_by(self, entity, sort):
        if sort['attr'] in entity.__mapper__.class_manager.keys():
            try:
                attr = getattr(entity, sort['attr'])
            except AttributeError:
                pass
            else:
                property_ = attr.property
                if isinstance(property_, ColumnProperty):
                    if isinstance(attr.property.columns[0], Label):
                        attr = attr.property.columns[0].name

                return self.query.order_by(sort['func'](attr))
        return self.query

    def parse_sort_arg(self, arg):
        if arg[0] == self.separator:
            func = desc
            arg = arg[1:]
        else:
            func = asc

        parts = arg.split(self.separator)
        return {
            'entity': parts[0] if len(parts) > 1 else None,
            'attr': parts[1] if len(parts) > 1 else arg,
            'func': func
        }

    def __call__(self, query, *args):
        self.query = query
        self.inspect_labels_and_entities()
        for sort in args:
            self.query = self.assign_order_by(sort)
        return self.query


def sort_query(query, *args):
    """
    Applies an sql ORDER BY for given query. This function can be easily used
    with user-defined sorting.

    The examples use the following model definition:

        >>> import sqlalchemy as sa
        >>> from sqlalchemy import create_engine
        >>> from sqlalchemy.orm import sessionmaker
        >>> from sqlalchemy.ext.declarative import declarative_base
        >>> from sqlalchemy_utils import sort_query
        >>>
        >>>
        >>> engine = create_engine(
        ...     'sqlite:///'
        ... )
        >>> Base = declarative_base()
        >>> Session = sessionmaker(bind=engine)
        >>> session = Session()
        >>>
        >>> class Category(Base):
        ...     __tablename__ = 'category'
        ...     id = sa.Column(sa.Integer, primary_key=True)
        ...     name = sa.Column(sa.Unicode(255))
        >>>
        >>> class Article(Base):
        ...     __tablename__ = 'article'
        ...     id = sa.Column(sa.Integer, primary_key=True)
        ...     name = sa.Column(sa.Unicode(255))
        ...     category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))
        ...
        ...     category = sa.orm.relationship(
        ...         Category, primaryjoin=category_id == Category.id
        ...     )



    1. Applying simple ascending sort

        >>> query = session.query(Article)
        >>> query = sort_query(query, 'name')

    2. Appying descending sort

        >>> query = sort_query(query, '-name')

    3. Applying sort to custom calculated label

        >>> query = session.query(
        ...     Category, db.func.count(Article.id).label('articles')
        ... )
        >>> query = sort_query(query, 'articles')

    4. Applying sort to joined table column

        >>> query = session.query(Article).join(Article.category)
        >>> query = sort_query(query, 'category-name')


    :param query: query to be modified
    :param sort: string that defines the label or column to sort the query by
    :param errors: whether or not to raise exceptions if unknown sort column
                   is passed
    """

    return QuerySorter()(query, *args)


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


def table_name(class_):
    """
    Return table name of given declarative class.
    """
    try:
        return class_.__tablename__
    except AttributeError:
        return class_.__table__.name


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


def batch_fetch(entities, *attr_paths):
    """
    Batch fetch given relationship attribute for collection of entities.

    This function is in many cases a valid alternative for SQLAlchemy's
    subqueryload and performs lot better.

    :param entities: list of entities of the same type
    :param attr:
        Either InstrumentedAttribute object or a string representing the name
        of the instrumented attribute

    Example::


        from sqlalchemy_utils import batch_fetch


        users = session.query(User).limit(20).all()

        batch_fetch(users, User.phonenumbers)


    Function also accepts strings as attribute names: ::


        users = session.query(User).limit(20).all()

        batch_fetch(users, 'phonenumbers')


    Multiple attributes may be provided: ::


        clubs = session.query(Club).limit(20).all()

        batch_fetch(
            clubs,
            'teams',
            'teams.players',
            'teams.players.user_groups'
        )

    You can also force populate backrefs: ::


        clubs = session.query(Club).limit(20).all()

        batch_fetch(
            clubs,
            'teams',
            'teams.players',
            'teams.players.user_groups -pb'
        )

    """

    if entities:
        first = entities[0]
        parent_ids = [entity.id for entity in entities]

        for attr_path in attr_paths:
            parent_dict = dict((entity.id, []) for entity in entities)
            populate_backrefs = False

            if isinstance(attr_path, six.string_types):
                attrs = attr_path.split('.')

                if len(attrs) > 1:
                    related_entities = []
                    for entity in entities:
                        related_entities.extend(getattr(entity, attrs[0]))

                    batch_fetch(
                        related_entities,
                        '.'.join(attrs[1:])
                    )
                    continue
                else:
                    args = attrs[-1].split(' ')
                    if '-pb' in args:
                        populate_backrefs = True

                    attr = getattr(
                        first.__class__, args[0]
                    )
            else:
                attr = attr_path

            prop = attr.property
            if not isinstance(prop, RelationshipProperty):
                raise Exception(
                    'Given attribute is not a relationship property.'
                )

            model = prop.mapper.class_

            session = object_session(first)

            if prop.secondary is None:
                if len(prop.remote_side) > 1:
                    raise Exception(
                        'Only relationships with single remote side columns '
                        'are supported.'
                    )

                column_name = list(prop.remote_side)[0].name

                related_entities = (
                    session.query(model)
                    .filter(
                        getattr(model, column_name).in_(parent_ids)
                    )
                )

                for entity in related_entities:
                    parent_dict[getattr(entity, column_name)].append(
                        entity
                    )

            else:
                column_name = None
                for column in prop.remote_side:
                    for fk in column.foreign_keys:
                        # TODO: make this support inherited tables
                        if fk.column.table == first.__class__.__table__:
                            column_name = fk.parent.name
                            break
                    if column_name:
                        break

                related_entities = (
                    session
                    .query(model, getattr(prop.secondary.c, column_name))
                    .join(
                        prop.secondary, prop.secondaryjoin
                    )
                    .filter(
                        getattr(prop.secondary.c, column_name).in_(
                            parent_ids
                        )
                    )
                )
                for entity, parent_id in related_entities:
                    parent_dict[parent_id].append(
                        entity
                    )

            for entity in entities:
                set_committed_value(
                    entity, prop.key, parent_dict[entity.id]
                )
            if populate_backrefs:
                backref_dict = dict(
                    (entity.id, []) for entity, parent_id in related_entities
                )
                for entity, parent_id in related_entities:
                    backref_dict[entity.id].append(
                        session.query(first.__class__).get(parent_id)
                    )
                for entity, parent_id in related_entities:
                    set_committed_value(
                        entity, prop.back_populates, backref_dict[entity.id]
                    )
