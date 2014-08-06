import sqlalchemy as sa
from sqlalchemy.orm.properties import ColumnProperty, SynonymProperty
from sqlalchemy.sql.expression import desc, asc, Label
from sqlalchemy.orm.util import AliasedInsp
from .orm import (
    get_attrs,
    get_expr_attr,
    get_hybrid_properties,
    get_query_entity_by_alias,
    get_query_entities,
    query_labels,
)


class QuerySorterException(Exception):
    pass


class QuerySorter(object):
    def __init__(self, silent=True, separator='-'):
        self.labels = []
        self.separator = separator
        self.silent = silent

    def assign_order_by(self, entity, attr, func):
        expr = None
        if attr in self.labels:
            expr = attr
        else:
            entity = get_query_entity_by_alias(self.query, entity)
            if entity:
                expr = self.order_by_attr(entity, attr)

        if expr is not None:
            return self.query.order_by(func(expr))
        if not self.silent:
            raise QuerySorterException(
                "Could not sort query with expression '%s'" % attr
            )
        return self.query

    def order_by_attr(self, entity, attr):
        properties = get_attrs(entity)
        if attr in properties:
            property_ = properties[attr]

            if isinstance(property_, ColumnProperty):
                if isinstance(property_.columns[0], Label):
                    return getattr(entity, property_.key)
                else:
                    return get_expr_attr(entity, property_)
            elif isinstance(property_, SynonymProperty):
                return get_expr_attr(entity, property_)
            return

        mapper = sa.inspect(entity)
        entity = mapper.entity

        if isinstance(mapper, AliasedInsp):
            mapper = mapper.mapper

        for key in get_hybrid_properties(mapper).keys():
            if attr == key:
                return getattr(entity, attr)

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
        self.labels = query_labels(query)

        for sort in args:
            if not sort:
                continue
            self.query = self.assign_order_by(
                **self.parse_sort_arg(sort)
            )
        return self.query


def sort_query(query, *args, **kwargs):
    """
    Applies an sql ORDER BY for given query. This function can be easily used
    with user-defined sorting.

    The examples use the following model definition:

    ::


        import sqlalchemy as sa
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy_utils import sort_query


        engine = create_engine(
            'sqlite:///'
        )
        Base = declarative_base()
        Session = sessionmaker(bind=engine)
        session = Session()

        class Category(Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category, primaryjoin=category_id == Category.id
            )



    1. Applying simple ascending sort
    ::


        query = session.query(Article)
        query = sort_query(query, 'name')


    2. Appying descending sort
    ::


        query = sort_query(query, '-name')

    3. Applying sort to custom calculated label
    ::


        query = session.query(
            Category, sa.func.count(Article.id).label('articles')
        )
        query = sort_query(query, 'articles')

    4. Applying sort to joined table column
    ::


        query = session.query(Article).join(Article.category)
        query = sort_query(query, 'category-name')


    :param query:
        query to be modified
    :param sort:
        string that defines the label or column to sort the query by
    :param silent:
        Whether or not to raise exceptions if unknown sort column
        is passed. By default this is `True` indicating that no errors should
        be raised for unknown columns.
    """
    return QuerySorter(**kwargs)(query, *args)
