import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import metadata
else:
    from importlib_metadata import metadata


_sqlalchemy_version = tuple(
    [int(i) for i in metadata("sqlalchemy")["Version"].split(".")[:2]]
)


# In sqlalchemy 2.0, some functions moved to sqlalchemy.orm.
# In sqlalchemy 1.3, they are only available in .ext.declarative.
# In sqlalchemy 1.4, they are available in both places.
#
# WARNING
# -------
#
# These imports are for internal, private compatibility.
# They are not supported and may change or move at any time.
# Do not import these in your own code.
#

if _sqlalchemy_version >= (1, 4):
    from sqlalchemy.orm import declarative_base as _declarative_base
    from sqlalchemy.orm import synonym_for as _synonym_for
else:
    from sqlalchemy.ext.declarative import \
        declarative_base as _declarative_base
    from sqlalchemy.ext.declarative import synonym_for as _synonym_for


# scalar subqueries
if _sqlalchemy_version >= (1, 4):
    def get_scalar_subquery(query):
        return query.scalar_subquery()
else:
    def get_scalar_subquery(query):
        return query.as_scalar()


# In sqlalchemy 2.0, select() columns are positional.
# In sqlalchemy 1.3, select() columns must be wrapped in a list.
#
# _select_args() is designed so its return value can be unpacked:
#
#     select(*_select_args(1, 2))
#
# When sqlalchemy 1.3 support is dropped, remove the call to _select_args()
# and keep the arguments the same:
#
#     select(1, 2)
#
# WARNING
# -------
#
# _select_args() is a private, internal function.
# It is not supported and may change or move at any time.
# Do not import this in your own code.
#
if _sqlalchemy_version >= (1, 4):
    def _select_args(*args):
        return args
else:
    def _select_args(*args):
        return [args]


__all__ = (
    "_declarative_base",
    "get_scalar_subquery",
    "_select_args",
    "_synonym_for",
)
