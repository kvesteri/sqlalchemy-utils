from collections import defaultdict
from itertools import chain
import six
import sqlalchemy as sa
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.attributes import (
    set_committed_value, InstrumentedAttribute
)
from sqlalchemy.orm.session import object_session
from sqlalchemy_utils.generic import GenericRelationshipProperty
from sqlalchemy_utils.functions.orm import (
    list_local_values,
    list_local_remote_exprs,
    local_values,
    remote_column_names,
    remote_values,
    remote
)


class PathException(Exception):
    pass


class DataException(Exception):
    pass


class with_backrefs(object):
    """
    Marks given attribute path so that whenever its fetched with batch_fetch
    the backref relations are force set too. Very useful when dealing with
    certain many-to-many relationship scenarios.
    """
    def __init__(self, path):
        self.path = path


class Path(object):
    """
    A class that represents an attribute path.
    """
    def __init__(self, entities, prop, populate_backrefs=False):
        self.validate_property(prop)
        self.property = prop
        self.entities = entities
        self.populate_backrefs = populate_backrefs
        self.fetcher = self.fetcher_class(self)

    def validate_property(self, prop):
        if (
            not isinstance(prop, RelationshipProperty) and
            not isinstance(prop, GenericRelationshipProperty)
        ):
            raise PathException(
                'Given attribute is not a relationship property.'
            )

    @property
    def session(self):
        return object_session(self.entities[0])

    @property
    def model(self):
        return self.property.mapper.class_

    @classmethod
    def parse(cls, entities, path, populate_backrefs=False):
        if isinstance(path, six.string_types):
            attrs = path.split('.')

            if len(attrs) > 1:
                related_entities = []
                for entity in entities:
                    related_entities.extend(getattr(entity, attrs[0]))

                if not related_entities:
                    raise DataException('No related entities.')

                subpath = '.'.join(attrs[1:])
                return Path.parse(related_entities, subpath, populate_backrefs)
            else:
                attr = getattr(
                    entities[0].__class__, attrs[0]
                )
        elif isinstance(path, InstrumentedAttribute):
            attr = path
        else:
            raise PathException('Unknown path type.')

        return Path(entities, attr.property, populate_backrefs)

    @property
    def fetcher_class(self):
        if isinstance(self.property, GenericRelationshipProperty):
            return GenericRelationshipFetcher
        else:
            if self.property.secondary is not None:
                return ManyToManyFetcher
            else:
                if self.property.direction.name == 'MANYTOONE':
                    return ManyToOneFetcher
                else:
                    return OneToManyFetcher


def batch_fetch(entities, *attr_paths):
    """
    Batch fetch given relationship attribute for collection of entities.

    This function is in many cases a valid alternative for SQLAlchemy's
    subqueryload and performs lot better.

    :param entities: list of entities of the same type
    :param attr_paths:
        List of either InstrumentedAttribute objects or a strings representing
        the name of the instrumented attribute

    Example::


        from sqlalchemy_utils import batch_fetch


        users = session.query(User).limit(20).all()

        batch_fetch(users, User.phonenumbers)


    Function also accepts strings as attribute names: ::


        users = session.query(User).limit(20).all()

        batch_fetch(users, 'phonenumbers')


    Multiple attributes may be provided: ::


        clubs = session.query(Club).limit(20).all()

        batch_fetch(
            clubs,
            'teams',
            'teams.players',
            'teams.players.user_groups'
        )

    You can also force populate backrefs: ::


        from sqlalchemy_utils import with_backrefs


        clubs = session.query(Club).limit(20).all()

        batch_fetch(
            clubs,
            'teams',
            'teams.players',
            with_backrefs('teams.players.user_groups')
        )

    """

    if entities:
        for path in attr_paths:
            try:
                fetcher = fetcher_factory(entities, path)
                fetcher.fetch()
                fetcher.populate()
            except DataException:
                pass


def get_fetcher(entities, path, populate_backrefs):
    return Path.parse(entities, path, populate_backrefs).fetcher


def fetcher_factory(entities, path):
    populate_backrefs = False
    if isinstance(path, with_backrefs):
        path = path.path
        populate_backrefs = True

    if isinstance(path, tuple):
        return CompositeFetcher(
            *(get_fetcher(entities, p, populate_backrefs) for p in path)
        )
    else:
        return get_fetcher(entities, path, populate_backrefs)


class CompositeFetcher(object):
    def __init__(self, *fetchers):
        if not all(
            fetchers[0].path.model == fetcher.path.model
            for fetcher in fetchers
        ):
            raise PathException(
                'Each relationship property must have the same class when '
                'using CompositeFetcher.'
            )
        self.fetchers = fetchers

    @property
    def session(self):
        return self.fetchers[0].path.session

    @property
    def model(self):
        return self.fetchers[0].path.model

    @property
    def condition(self):
        return sa.or_(
            *(fetcher.condition for fetcher in self.fetchers)
        )

    @property
    def related_entities(self):
        return self.session.query(self.model).filter(self.condition)

    def fetch(self):
        for entity in self.related_entities:
            for fetcher in self.fetchers:
                if any(remote_values(fetcher.prop, entity)):
                    fetcher.append_entity(entity)

    def populate(self):
        for fetcher in self.fetchers:
            fetcher.populate()


class Fetcher(object):
    def __init__(self, path):
        self.path = path
        self.prop = self.path.property

        default = list if self.prop.uselist else lambda: None
        self.parent_dict = defaultdict(default)

    @property
    def relation_query_base(self):
        return self.path.session.query(self.path.model)

    @property
    def related_entities(self):
        return self.relation_query_base.filter(self.condition)

    def populate_backrefs(self, related_entities):
        """
        Populates backrefs for given related entities.
        """
        backref_dict = dict(
            (local_values(self.prop, value[0]), [])
            for value in related_entities
        )
        for value in related_entities:
            backref_dict[local_values(self.prop, value[0])].append(
                self.path.session.query(self.path.entities[0].__class__).get(
                    tuple(value[1:])
                )
            )
        for value in related_entities:
            set_committed_value(
                value[0],
                self.prop.back_populates,
                backref_dict[local_values(self.prop, value[0])]
            )

    def populate(self):
        """
        Populate batch fetched entities to parent objects.
        """
        for entity in self.path.entities:
            set_committed_value(
                entity,
                self.prop.key,
                self.parent_dict[local_values(self.prop, entity)]
            )

        if self.path.populate_backrefs:
            self.populate_backrefs(self.related_entities)

    @property
    def condition(self):
        names = list(remote_column_names(self.prop))
        if len(names) == 1:
            attr = getattr(remote(self.prop), names[0])
            return attr.in_(
                v[0] for v in list_local_values(self.prop, self.path.entities)
            )
        elif len(names) > 1:
            return sa.or_(
                *list_local_remote_exprs(self.prop, self.path.entities)
            )
        else:
            raise PathException(
                'Could not obtain remote column names.'
            )

    def fetch(self):
        for entity in self.related_entities:
            self.append_entity(entity)


class GenericRelationshipFetcher(object):
    def __init__(self, path):
        self.path = path
        self.prop = self.path.property
        self.parent_dict = defaultdict(lambda: None)

    def fetch(self):
        for entity in self.related_entities:
            self.append_entity(entity)

    def append_entity(self, entity):
        self.parent_dict[remote_values(self.prop, entity)] = entity

    def populate(self):
        """
        Populate batch fetched entities to parent objects.
        """
        for entity in self.path.entities:
            set_committed_value(
                entity,
                self.prop.key,
                self.parent_dict[local_values(self.prop, entity)]
            )

    @property
    def related_entities(self):
        id_dict = defaultdict(list)
        for entity in self.path.entities:
            discriminator = getattr(entity, self.prop._discriminator_col.key)
            for id_col in self.prop._id_cols:
                id_dict[discriminator].append(
                    getattr(entity, id_col.key)
                )
        return chain(*self._queries(sa.inspect(entity), id_dict))

    def _queries(self, state, id_dict):
        for discriminator, ids in six.iteritems(id_dict):
            class_ = state.class_._decl_class_registry.get(discriminator)
            yield self.path.session.query(
                class_
            ).filter(
                class_.id.in_(ids)
            )


class ManyToManyFetcher(Fetcher):
    @property
    def relation_query_base(self):
        return (
            self.path.session
            .query(
                self.path.model,
                *[
                    getattr(remote(self.prop), name)
                    for name in remote_column_names(self.prop)
                ]
            )
            .join(
                self.prop.secondary, self.prop.secondaryjoin
            )
        )

    def fetch(self):
        for value in self.related_entities:
            self.parent_dict[tuple(value[1:])].append(
                value[0]
            )


class ManyToOneFetcher(Fetcher):
    def append_entity(self, entity):
        self.parent_dict[remote_values(self.prop, entity)] = entity


class OneToManyFetcher(Fetcher):
    def append_entity(self, entity):
        self.parent_dict[remote_values(self.prop, entity)].append(
            entity
        )
