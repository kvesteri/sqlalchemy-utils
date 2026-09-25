import builtins
from collections.abc import Iterable

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.orm import object_session

from .exceptions import ImproperlyConfigured
from .functions import identity


class GenericComparator(Comparator):
    def __init__(self, relationship, cls):
        self.relationship = relationship
        self.cls = cls

    def __clause_element__(self):
        raise NotImplementedError(
            'A generic relationship can only be compared against a model '
            'instance or with is_type().'
        )

    def __eq__(self, other):
        discriminator, ids = self.relationship._attributes(self.cls)
        q = discriminator == type(other).__name__
        for column, value in zip(ids, identity(other)):
            q &= column == value
        return q

    def __ne__(self, other):
        return ~(self == other)

    def is_type(self, other):
        discriminator, _ = self.relationship._attributes(self.cls)
        class_names = [
            mapper.class_.__name__ for mapper in sa.inspect(other).self_and_descendants
        ]
        return discriminator.in_(class_names)


class GenericRelationship:
    """A generic form of the relationship property.

    Creates a 1 to many relationship between the parent model
    and any other models using a discriminator (the class name).

    Implemented as a hybrid property on top of the discriminator and id
    attributes, so it only relies on public SQLAlchemy APIs.

    :param discriminator:
        Field to discriminate which model we are referring to.
    :param id:
        Field to point to the model we are referring to.
    """

    def __init__(self, discriminator, id):
        self.discriminator = discriminator
        if isinstance(id, Iterable) and not isinstance(id, str):
            self.ids = list(id)
        else:
            self.ids = [id]
        # Key for caching the assigned target object on the instance dict.
        self.cache_key = f'_generic_relationship_{builtins.id(self)}'

    def _key(self, cls, column):
        if isinstance(column, str):
            return column
        if isinstance(column, hybrid_property):
            return column.__name__
        try:
            return sa.inspect(cls).get_property_by_column(column).key
        except sa.orm.exc.UnmappedColumnError:
            raise ImproperlyConfigured(
                f'Could not find generic relationship attribute for {column!r}.'
            )

    def _keys(self, cls):
        return (
            self._key(cls, self.discriminator),
            [self._key(cls, column) for column in self.ids],
        )

    def _attributes(self, cls):
        discriminator, ids = self._keys(cls)
        return getattr(cls, discriminator), [getattr(cls, key) for key in ids]

    def _target_class(self, cls, discriminator):
        for mapper in sa.inspect(cls).registry.mappers:
            if mapper.class_.__name__ == discriminator:
                return mapper.class_

    def get(self, obj):
        discriminator_key, id_keys = self._keys(type(obj))
        discriminator = getattr(obj, discriminator_key)
        id = tuple(getattr(obj, key) for key in id_keys)

        # Return the object assigned to this relationship as long as the
        # discriminator and id still point to it.
        cached = obj.__dict__.get(self.cache_key)
        if (
            cached is not None
            and type(cached).__name__ == discriminator
            and identity(cached) == id
        ):
            return cached

        # Use the session the object is bound to in order to perform
        # a lazy query for the target.
        session = object_session(obj)
        if session is None:
            return None

        target_class = self._target_class(type(obj), discriminator)
        if target_class is None:
            # Unknown discriminator; return nothing.
            return None

        return session.get(target_class, id)

    def set(self, obj, value):
        discriminator_key, id_keys = self._keys(type(obj))
        obj.__dict__[self.cache_key] = value

        if value is None:
            # Nullify relationship args
            for key in id_keys:
                setattr(obj, key, None)
            setattr(obj, discriminator_key, None)
        else:
            for key, pk in zip(id_keys, identity(value)):
                setattr(obj, key, pk)
            setattr(obj, discriminator_key, type(value).__name__)

    def comparator(self, cls):
        return GenericComparator(self, cls)


def generic_relationship(discriminator, id, doc=None):
    relationship = GenericRelationship(discriminator, id)
    prop = hybrid_property(
        relationship.get,
        relationship.set,
        custom_comparator=relationship.comparator,
    )
    prop.__doc__ = doc
    return prop
