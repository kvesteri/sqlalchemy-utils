import sqlalchemy as sa


def select_aggregate(agg_expr, relationships):
    """
    Return a subquery for fetching an aggregate value of given aggregate
    expression and given sequence of relationships.

    The returned aggregate query can be used when updating denormalized column
    value with query such as:

    UPDATE table SET column = {aggregate_query}
    WHERE {condition}

    :param agg_expr:
        an expression to be selected, for example sa.func.count('1')
    :param relationships:
        Sequence of relationships to be used for building the aggregate
        query.
    """
    from_ = relationships[0].mapper.class_.__table__
    for relationship in relationships[0:-1]:
        property_ = relationship.property
        if property_.secondary is not None:
            from_ = from_.join(
                property_.secondary,
                property_.secondaryjoin
            )

        from_ = (
            from_
            .join(
                property_.parent.class_,
                property_.primaryjoin
            )
        )

    prop = relationships[-1].property
    condition = prop.primaryjoin
    if prop.secondary is not None:
        from_ = from_.join(
            prop.secondary,
            prop.secondaryjoin
        )

    query = sa.select(
        [agg_expr],
        from_obj=[from_]
    )

    return query.where(condition)
