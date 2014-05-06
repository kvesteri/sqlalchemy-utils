"""
QueryChain is a wrapper for sequence of queries.


Features:

    * Easy iteration for sequence of queries
    * Limit and offset which are applied to all queries in the chain
    * Smart __getitem__ support


Initialization
^^^^^^^^^^^^^^

QueryChain takes iterable of queries as first argument. Additionally limit and
offset parameters can be given

::

    chain = QueryChain([session.query(User), session.query(Article)])

    chain = QueryChain(
        [session.query(User), session.query(Article)],
        limit=4
    )


Simple iteration
^^^^^^^^^^^^^^^^
::

    chain = QueryChain([session.query(User), session.query(Article)])

    for obj in chain:
        print obj


Limit and offset
^^^^^^^^^^^^^^^^

Lets say you have 5 blog posts, 5 articles and 5 news items in your
database.

::

    chain = QueryChain(
        [
            session.query(BlogPost),
            session.query(Article),
            session.query(NewsItem)
        ],
        limit=5
    )

    list(chain)  # all blog posts but not articles and news items


    chain.offset = 4
    list(chain)  # last blog post, and first four articles


Chain slicing
^^^^^^^^^^^^^

::

    chain = QueryChain(
        [
            session.query(BlogPost),
            session.query(Article),
            session.query(NewsItem)
        ]
    )

    chain[3:6]   # New QueryChain with offset=3 and limit=6
"""
from copy import copy


class QueryChain(object):
    """
    QueryChain can be used as a wrapper for sequence of queries.

    :param queries: A sequence of SQLAlchemy Query objects
    :param limit: Similar to normal query limit this parameter can be used for
        limiting the number of results for the whole query chain.
    :param offset: Similar to normal query offset this parameter can be used
        for offsetting the query chain as a whole.

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

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.__class__(
                queries=self.queries,
                limit=key.stop,
                offset=key.start
            )
        else:
            for obj in self[key:1]:
                return obj

    def __repr__(self):
        return '<QueryChain at 0x%x>' % id(self)
