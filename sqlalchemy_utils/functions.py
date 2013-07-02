from sqlalchemy.orm import defer
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.util import AliasedInsp
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
        print sort
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
