from copy import copy


class QueryChain(object):
    """
    :param queries: A sequence of SQLAlchemy Query objects
    :param limit: Similar to normal query limit this parameter can be used for
        limiting the number of results for the whole query chain.
    :param offset: Similar to normal query offset this parameter can be used
        for offsetting the query chain as a whole.

    ::

        chain = QueryChain([session.query(User), session.query(Article)])

        for obj in chain[0:5]:
            print obj

    .. versionadded: 0.26.0
    """
    def __init__(self, queries, limit=None, offset=None):
        self.queries = queries
        self.limit = limit
        self.offset = offset

    def __iter__(self):
        consumed = 0
        skipped = 0
        for query in self.queries:
            query_copy = copy(query)
            if self.limit:
                query = query.limit(self.limit - consumed)
            if self.offset:
                query = query.offset(self.offset - skipped)

            obj_count = 0
            for obj in query:
                consumed += 1
                obj_count += 1
                yield obj

            if not obj_count:
                skipped += query_copy.count()
            else:
                skipped += obj_count

    def __repr__(self):
        return '<QueryChain at 0x%x>' % id(self)
