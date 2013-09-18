from collections import defaultdict
import six
import sqlalchemy as sa
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.attributes import (
    set_committed_value, InstrumentedAttribute
)
from sqlalchemy.orm.session import object_session


class PathException(Exception):
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
        self.property = prop
        self.entities = entities
        self.populate_backrefs = populate_backrefs
        if not isinstance(self.property, RelationshipProperty):
            raise PathException(
                'Given attribute is not a relationship property.'
            )
        self.fetcher = self.fetcher_class(self)

    @property
    def session(self):
        return object_session(self.entities[0])

    @property
    def parent_model(self):
        return self.entities[0].__class__

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
                    return
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
        if self.property.secondary is not None:
            return ManyToManyFetcher
        else:
            if self.property.direction.name == 'MANYTOONE':
                return ManyToOneFetcher
            else:
                return OneToManyFetcher


class CompositePath(object):
    def __init__(self, *paths):
        self.paths = paths


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
            fetcher = fetcher_factory(entities, path)
            if fetcher:
                fetcher.fetch()
                fetcher.populate()


def fetcher_factory(entities, path):
    populate_backrefs = False
    if isinstance(path, with_backrefs):
        path = path.path
        populate_backrefs = True

    if isinstance(path, CompositePath):
        fetchers = []
        for path in path.paths:
            path = Path.parse(entities, path, populate_backrefs)
            if path:
                fetchers.append(
                    path.fetcher
                )

        return CompositeFetcher(*fetchers)
    else:
        path = Path.parse(entities, path, populate_backrefs)
        if path:
            return path.fetcher


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
            *[fetcher.condition for fetcher in self.fetchers]
        )

    @property
    def related_entities(self):
        return self.session.query(self.model).filter(self.condition)

    def fetch(self):
        for entity in self.related_entities:
            for fetcher in self.fetchers:
                if any(
                    getattr(entity, name)
                    for name in fetcher.remote_column_names
                ):
                    fetcher.append_entity(entity)

    def populate(self):
        for fetcher in self.fetchers:
            fetcher.populate()


class Fetcher(object):
    def __init__(self, path):
        self.path = path
        self.prop = self.path.property
        if self.prop.uselist:
            self.parent_dict = defaultdict(list)
        else:
            self.parent_dict = defaultdict(lambda: None)

    @property
    def local_values_list(self):
        return [
            self.local_values(entity)
            for entity in self.path.entities
        ]

    @property
    def relation_query_base(self):
        return self.path.session.query(self.path.model)

    @property
    def related_entities(self):
        return self.relation_query_base.filter(self.condition)

    @property
    def local_column_names(self):
        return [local.name for local, remote in self.prop.local_remote_pairs]

    def parent_key(self, entity):
        return tuple(
            getattr(entity, name)
            for name in self.remote_column_names
        )

    def local_values(self, entity):
        return tuple(
            getattr(entity, name)
            for name in self.local_column_names
        )

    def populate_backrefs(self, related_entities):
        """
        Populates backrefs for given related entities.
        """
        backref_dict = dict(
            (self.local_values(value[0]), [])
            for value in related_entities
        )
        for value in related_entities:
            backref_dict[self.local_values(value[0])].append(
                self.path.session.query(self.path.parent_model).get(
                    tuple(value[1:])
                )
            )
        for value in related_entities:
            set_committed_value(
                value[0],
                self.prop.back_populates,
                backref_dict[self.local_values(value[0])]
            )

    def populate(self):
        """
        Populate batch fetched entities to parent objects.
        """
        for entity in self.path.entities:
            set_committed_value(
                entity,
                self.prop.key,
                self.parent_dict[self.local_values(entity)]
            )

        if self.path.populate_backrefs:
            self.populate_backrefs(self.related_entities)

    @property
    def remote(self):
        return self.path.model

    @property
    def condition(self):
        names = self.remote_column_names
        if len(names) == 1:
            return getattr(self.remote, names[0]).in_(
                value[0] for value in self.local_values_list
            )
        elif len(names) > 1:
            conditions = []
            for entity in self.path.entities:
                conditions.append(
                    sa.and_(
                        *[
                            getattr(self.remote, remote.name)
                            ==
                            getattr(entity, local.name)
                            for local, remote in self.prop.local_remote_pairs
                            if remote in self.remote_column_names
                        ]
                    )
                )
            return sa.or_(*conditions)
        else:
            raise PathException(
                'Could not obtain remote column names.'
            )

    def fetch(self):
        for entity in self.related_entities:
            self.append_entity(entity)

    @property
    def remote_column_names(self):
        return [remote.name for local, remote in self.prop.local_remote_pairs]


class ManyToManyFetcher(Fetcher):
    @property
    def remote(self):
        return self.prop.secondary.c

    @property
    def local_column_names(self):
        names = []
        for local, remote in self.prop.local_remote_pairs:
            for fk in remote.foreign_keys:
                if fk.column.table in self.prop.parent.tables:
                    names.append(local.name)
        return names

    @property
    def remote_column_names(self):
        names = []
        for local, remote in self.prop.local_remote_pairs:
            for fk in remote.foreign_keys:
                if fk.column.table in self.prop.parent.tables:
                    names.append(remote.name)
        return names

    @property
    def relation_query_base(self):
        return (
            self.path.session
            .query(
                self.path.model,
                *[
                    getattr(self.prop.secondary.c, name)
                    for name in self.remote_column_names
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
        #print 'appending entity ', entity, ' to key ', self.parent_key(entity)
        self.parent_dict[self.parent_key(entity)] = entity


class OneToManyFetcher(Fetcher):
    def append_entity(self, entity):
        #print 'appending entity ', entity, ' to key ', self.parent_key(entity)
        self.parent_dict[self.parent_key(entity)].append(
            entity
        )
