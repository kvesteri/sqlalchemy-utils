def get_scalar_subquery(query):
    try:
        return query.scalar_subquery()
    except AttributeError:  # SQLAlchemy <1.4
        return query.as_scalar()
