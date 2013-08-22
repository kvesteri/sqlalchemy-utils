from collections import defaultdict
import six
import sqlalchemy as sa
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.orm.session import object_session


class with_backrefs(object):
    """
    Marks given attribute path so that whenever its fetched with batch_fetch
    the backref relations are force set too.
    """
    def __init__(self, attr_path):
        self.attr_path = attr_path


class compound_path(object):
    def __init__(self, *attr_paths):
        self.attr_paths = attr_paths


def batch_fetch(entities, *attr_paths):
    """
    Batch fetch given relationship attribute for collection of entities.

    This function is in many cases a valid alternative for SQLAlchemy's
    subqueryload and performs lot better.

    :param entities: list of entities of the same type
    :param attr:
        Either InstrumentedAttribute object or a string representing the name
        of the instrumented attribute

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
        fetcher = FetchingCoordinator(entities)
        for attr_path in attr_paths:
            fetcher(attr_path)


class FetchingCoordinator(object):
    def __init__(self, entities):
        self.entities = entities
        self.first = entities[0]
        self.session = object_session(self.first)

    def parse_attr_path(self, attr_path, should_populate_backrefs):
        if isinstance(attr_path, six.string_types):
            attrs = attr_path.split('.')

            if len(attrs) > 1:
                related_entities = []
                for entity in self.entities:
                    related_entities.extend(getattr(entity, attrs[0]))

                subpath = '.'.join(attrs[1:])

                if should_populate_backrefs:
                    subpath = with_backrefs(subpath)

                return self.__class__(related_entities).fetcher_for_attr_path(
                    subpath
                )
            else:
                attr_path = getattr(
                    self.first.__class__, attrs[0]
                )
        return self.fetcher_for_property(attr_path.property)

    def fetcher_for_property(self, property_):
        if not isinstance(property_, RelationshipProperty):
            raise Exception(
                'Given attribute is not a relationship property.'
            )

        if property_.secondary is not None:
            fetcher_class = ManyToManyFetcher
        else:
            if property_.direction.name == 'MANYTOONE':
                fetcher_class = ManyToOneFetcher
            else:
                fetcher_class = OneToManyFetcher

        return fetcher_class(
            self.entities,
            property_,
            self.should_populate_backrefs
        )

    def fetcher_for_attr_path(self, attr_path):
        if isinstance(attr_path, with_backrefs):
            self.should_populate_backrefs = True
            attr_path = attr_path.attr_path
        else:
            self.should_populate_backrefs = False

        return self.parse_attr_path(
            attr_path,
            self.should_populate_backrefs
        )

    def __call__(self, attr_path):
        if isinstance(attr_path, compound_path):
            fetchers = []
            for path in attr_path.attr_paths:
                fetchers.append(self.fetcher_for_attr_path(path))

            fetcher = CompoundFetcher(*fetchers)
            print fetcher.condition
        else:
            fetcher = self.fetcher_for_attr_path(attr_path)
            if not fetcher:
                return
            fetcher.fetch()
            fetcher.populate()


class CompoundFetcher(object):
    def __init__(self, *fetchers):
        if not all(fetchers[0].model == fetcher.model for fetcher in fetchers):
            raise Exception(
                'Each relationship property must have the same class when '
                'using CompoundFetcher.'
            )
        self.fetchers = fetchers

    @property
    def condition(self):
        return sa.or_(
            *[fetcher.condition for fetcher in self.fetchers]
        )

    @property
    def local_values(self):
        pass


class Fetcher(object):
    def __init__(self, entities, property_, populate_backrefs=False):
        self.should_populate_backrefs = populate_backrefs
        self.entities = entities
        self.prop = property_
        self.model = self.prop.mapper.class_
        self.first = self.entities[0]
        self.session = object_session(self.first)

    @property
    def local_values_list(self):
        return [
            self.local_values(entity)
            for entity in self.entities
        ]

    def local_values(self, entity):
        return getattr(entity, list(self.prop.local_columns)[0].name)

    def populate_backrefs(self, related_entities):
        """
        Populates backrefs for given related entities.
        """
        backref_dict = dict(
            (self.local_values(entity), [])
            for entity, parent_id in related_entities
        )
        for entity, parent_id in related_entities:
            backref_dict[self.local_values(entity)].append(
                self.session.query(self.first.__class__).get(parent_id)
            )
        for entity, parent_id in related_entities:
            set_committed_value(
                entity,
                self.prop.back_populates,
                backref_dict[self.local_values(entity)]
            )

    def populate(self):
        """
        Populate batch fetched entities to parent objects.
        """
        for entity in self.entities:
            set_committed_value(
                entity,
                self.prop.key,
                self.parent_dict[self.local_values(entity)]
            )

        if self.should_populate_backrefs:
            self.populate_backrefs(self.related_entities)

    @property
    def remote_column_name(self):
        return list(self.prop.remote_side)[0].name

    @property
    def condition(self):
        return getattr(self.model, self.remote_column_name).in_(
            self.local_values_list
        )

    @property
    def related_entities(self):
        return self.session.query(self.model).filter(self.condition)


class ManyToManyFetcher(Fetcher):
    @property
    def remote_column_name(self):
        for column in self.prop.remote_side:
            for fk in column.foreign_keys:
                # TODO: make this support inherited tables
                if fk.column.table == self.first.__class__.__table__:
                    return fk.parent.name

    @property
    def related_entities(self):
        return (
            self.session
            .query(
                self.model,
                getattr(self.prop.secondary.c, self.remote_column_name)
            )
            .join(
                self.prop.secondary, self.prop.secondaryjoin
            )
            .filter(
                getattr(self.prop.secondary.c, self.remote_column_name).in_(
                    self.local_values_list
                )
            )
        )

    def fetch(self):
        self.parent_dict = defaultdict(list)
        for entity, parent_id in self.related_entities:
            self.parent_dict[parent_id].append(
                entity
            )


class ManyToOneFetcher(Fetcher):
    def fetch(self):
        self.parent_dict = defaultdict(lambda: None)
        for entity in self.related_entities:
            self.parent_dict[getattr(entity, self.remote_column_name)] = entity


class OneToManyFetcher(Fetcher):
    def fetch(self):
        self.parent_dict = defaultdict(list)
        for entity in self.related_entities:
            self.parent_dict[getattr(entity, self.remote_column_name)].append(
                entity
            )
