import sqlalchemy as sa


class CaseInsensitiveComparator(sa.Unicode.Comparator):
    @classmethod
    def lowercase_arg(cls, func):
        def operation(self, other, **kwargs):
            if other is None:
                return getattr(sa.Unicode.Comparator, func)(
                    self, other, **kwargs
                )
            return getattr(sa.Unicode.Comparator, func)(
                self, sa.func.lower(other), **kwargs
            )
        return operation

    def in_(self, other):
        if isinstance(other, list) or isinstance(other, tuple):
            other = map(sa.func.lower, other)
        return sa.Unicode.Comparator.in_(self, other)

    def notin_(self, other):
        if isinstance(other, list) or isinstance(other, tuple):
            other = map(sa.func.lower, other)
        return sa.Unicode.Comparator.notin_(self, other)


string_operator_funcs = [
    '__eq__',
    '__ne__',
    '__lt__',
    '__le__',
    '__gt__',
    '__ge__',
    'concat',
    'contains',
    'ilike',
    'like',
    'notlike',
    'notilike',
    'startswith',
    'endswith',
]

for func in string_operator_funcs:
    setattr(
        CaseInsensitiveComparator,
        func,
        CaseInsensitiveComparator.lowercase_arg(func)
    )
