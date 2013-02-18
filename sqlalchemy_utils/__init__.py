from flask import request
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.sql.expression import desc, asc


def sort_query(query, sort):
    """
    Applies an sql ORDER BY for given query

    :param query: query to be modified
    :param sort: string that defines the label or column to sort the query by
    """
    entities = [entity.entity_zero.class_ for entity in query._entities]
    for mapper in query._join_entities:
        if isinstance(mapper, Mapper):
            entities.append(mapper.class_)
        else:
            entities.append(mapper)

    # get all label names for queries such as:
    # db.session.query(Category, db.func.count(Article.id).label('articles'))
    labels = []
    for entity in query._entities:
        if isinstance(entity, _ColumnEntity) and entity._label_name:
            labels.append(entity._label_name)

    sort = request.args.get('sort', sort)
    if not sort:
        return query

    if sort[0] == '-':
        func = desc
        sort = sort[1:]
    else:
        func = asc

    component = None
    parts = sort.split('-')
    if len(parts) > 1:
        component = parts[0]
        sort = parts[1]
    if sort in labels:
        query = query.order_by(func(sort))
    else:
        for entity in entities:
            if component and entity.__table__.name != component:
                continue
            if sort in entity.__table__.columns:
                try:
                    attr = getattr(entity, sort)
                    query = query.order_by(func(attr))
                except AttributeError:
                    pass
                break
    return query


def escape_like(string, escape_char='*'):
    """
    Escapes the string paremeter used in SQL LIKE expressions

    :param string: a string to escape
    :param escape_char: escape character
    """
    return (
        string
        .replace(escape_char, escape_char * 2)
        .replace('%', escape_char + '%')
        .replace('_', escape_char + '_')
    )
