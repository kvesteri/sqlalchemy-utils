from collections import Iterable

import six

from sqlalchemy.orm.interfaces import MapperProperty, PropComparator
from sqlalchemy.orm.session import _state_session
from sqlalchemy.orm import attributes, class_mapper
from sqlalchemy.util import set_creation_order
from sqlalchemy_utils.functions import table_name, identity


def class_from_table_name(state, table):
    for class_ in state.class_._decl_class_registry.values():
        name = table_name(class_)
        if name and name == table:
            return class_
    return None


class GenericAttributeImpl(attributes.ScalarAttributeImpl):
    def get(self, state, dict_, passive=attributes.PASSIVE_OFF):
        if self.key in dict_:
            return dict_[self.key]

        # Retrieve the session bound to the state in order to perform
        # a lazy query for the attribute.
        session = _state_session(state)
        if session is None:
            # State is not bound to a session; we cannot proceed.
            return None

        # Find class for discriminator.
        # TODO: Perhaps optimize with some sort of lookup?
        discriminator = state.attrs[self.parent_token.discriminator.key].value
        target_class = class_from_table_name(state, discriminator)

        if target_class is None:
            # Unknown discriminator; return nothing.
            return None

        id = self.get_state_id(state)
        target = session.query(target_class).get(id)

        # Return found (or not found) target.
        return target

    def get_state_id(self, state):
        # Lookup row with the discriminator and id.
        return tuple(state.attrs[id.key].value for id in self.parent_token.id)

    def set(self, state, dict_, initiator,
            passive=attributes.PASSIVE_OFF,
            check_old=None,
            pop=False):

        # Set us on the state.
        dict_[self.key] = initiator

        if initiator is None:
            # Nullify relationship args
            for id in self.parent_token.id:
                dict_[id.key] = None
            dict_[self.parent_token.discriminator.key] = None
        else:
            # Get the primary key of the initiator and ensure we
            # can support this assignment.
            mapper = class_mapper(type(initiator))

            pk = mapper.identity_key_from_instance(initiator)[1]

            # Set the identifier and the discriminator.
            discriminator = table_name(initiator)

            for index, id in enumerate(self.parent_token.id):
                dict_[id.key] = pk[index]
            dict_[self.parent_token.discriminator.key] = discriminator


class GenericRelationshipProperty(MapperProperty):
    """A generic form of the relationship property.

    Creates a 1 to many relationship between the parent model
    and any other models using a descriminator (the table name).

    :param discriminator
        Field to discriminate which model we are referring to.
    :param id:
        Field to point to the model we are referring to.
    """

    def __init__(self, discriminator, id, doc=None):
        self._discriminator_col = discriminator
        self._id_cols = id
        self._id = None
        self._discriminator = None
        self.doc = doc

        set_creation_order(self)

    def _column_to_property(self, column):
        for name, attr in self.parent.attrs.items():
            other = self.parent.columns.get(name)
            if other is not None and column.name == other.name:
                return attr

    def init(self):
        def convert_strings(column):
            if isinstance(column, six.string_types):
                return self.parent.columns[column]
            return column

        self._discriminator_col = convert_strings(self._discriminator_col)
        self._id_cols = convert_strings(self._id_cols)

        if isinstance(self._id_cols, Iterable):
            self._id_cols = list(map(convert_strings, self._id_cols))
        else:
            self._id_cols = [self._id_cols]

        self.discriminator = self._column_to_property(self._discriminator_col)
        self.id = list(map(self._column_to_property, self._id_cols))

    class Comparator(PropComparator):

        def __init__(self, prop, parentmapper):
            self.property = prop
            self._parentmapper = parentmapper

        def __eq__(self, other):
            discriminator = table_name(other)
            q = self.property._discriminator_col == discriminator
            other_id = identity(other)
            for index, id in enumerate(self.property._id_cols):
                q &= id == other_id[index]
            return q

        def __ne__(self, other):
            return ~(self == other)

        def is_type(self, other):
            discriminator = table_name(other)
            return self.property._discriminator_col == discriminator

    def instrument_class(self, mapper):
        attributes.register_attribute(
            mapper.class_,
            self.key,
            comparator=self.Comparator(self, mapper),
            parententity=mapper,
            doc=self.doc,
            impl_class=GenericAttributeImpl,
            parent_token=self
        )


def generic_relationship(*args, **kwargs):
    return GenericRelationshipProperty(*args, **kwargs)
