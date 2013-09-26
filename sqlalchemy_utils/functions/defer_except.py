import six
from sqlalchemy import inspect
from sqlalchemy.orm import defer
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.orm.mapper import Mapper


def property_names(properties):
    names = []
    for property_ in properties:
        if isinstance(property_, six.string_types):
            names.append(property_)
        else:
            names.append(
                '%s.%s' % (
                    property_.class_.__name__,
                    property_.key
                )
            )
    return names


def query_entities(query):
    entities = []
    for entity in query._entities:
        if not isinstance(entity, _ColumnEntity):
            entities.append(entity.entity_zero.class_)

    for entity in query._join_entities:
        if isinstance(entity, Mapper):
            entities.append(entity.class_)
        else:
            entities.append(entity)
    return entities


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
    for property_ in inspect(model).attrs:
        if isinstance(property_, ColumnProperty):
            column = property_.columns[0]
            if column.name not in columns:
                query = query.options(defer(property_.key))
    return query
