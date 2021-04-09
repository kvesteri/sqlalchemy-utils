def get_scalar_subquery(query):
    try:
        return query.scalar_subquery()
    except AttributeError:
        return query.as_scalar()
