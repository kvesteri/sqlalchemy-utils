import six
from sqlalchemy import inspect
from sqlalchemy.orm import defer
from sqlalchemy.orm.properties import ColumnProperty


def property_names(properties):
    names = []
    for property_ in properties:
        if isinstance(property_, six.string_types):
            names.append(property_)
        else:
            names.append(property_.key)
    return names


def defer_except(query, properties):
    """
    Deferred loads all properties in given query, except the ones given.

    This function is very useful when working with models with myriad of
    properties and you want to deferred load many properties.

        >>> from sqlalchemy_utils import defer_except
        >>> query = session.query(Article)
        >>> query = defer_except(Article, [Article.id, Article.name])

    :param query: SQLAlchemy Query object to apply the deferred loading to
    :param properties: properties not to deferred load
    """

    allowed_names = property_names(properties)

    model = query._entities[0].entity_zero.class_
    for property_ in inspect(model).attrs:
        if isinstance(property_, ColumnProperty):
            if property_.key not in allowed_names:
                query = query.options(defer(property_.key))
    return query
