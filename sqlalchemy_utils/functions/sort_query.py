from sqlalchemy import inspect
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.orm.util import AliasedInsp
from sqlalchemy.sql.expression import desc, asc, Label


def attrs(expr):
    if isinstance(expr, AliasedInsp):
        return expr.mapper.attrs
    else:
        return inspect(expr).attrs


def sort_expression(expr, attr_name):
    if isinstance(expr, AliasedInsp):
        return getattr(expr.selectable.c, attr_name)
    else:
        return getattr(expr, attr_name)


def get_entity(expr):
    if isinstance(expr, AliasedInsp):
        return expr.mapper.class_
    elif isinstance(expr, Mapper):
        return expr.class_
    else:
        return expr


def matches_entity(alias, entity):
    if not alias:
        return True
    if isinstance(entity, AliasedInsp):
        name = entity.name
    else:
        name = entity.__table__.name

    return name == alias


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
            if not matches_entity(sort['entity'], entity):
                continue

            return self.assign_entity_attr_order_by(entity, sort)

        return self.query

    def assign_entity_attr_order_by(self, entity, sort):
        properties = attrs(entity)
        if sort['attr'] in properties:
            property_ = properties[sort['attr']]
            if isinstance(property_, ColumnProperty):
                if isinstance(property_.columns[0], Label):
                    expr = property_.columns[0].name
                else:
                    expr = sort_expression(entity, property_.key)
            return self.query.order_by(sort['func'](
                expr
            ))

        # Check hybrid properties.
        entity = get_entity(entity)
        if hasattr(entity, sort['attr']):
            return self.query.order_by(
                sort['func'](getattr(entity, sort['attr']))
            )
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

    ::


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
