import six
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

                batch_fetch(
                    related_entities,
                    subpath
                )
                return
            else:
                return getattr(
                    self.first.__class__, attrs[0]
                )
        else:
            return attr_path

    def fetch_relation_entities(self):
        if len(self.prop.remote_side) > 1:
            raise Exception(
                'Only relationships with single remote side columns '
                'are supported.'
            )

    def fetcher(self, property_):
        if not isinstance(property_, RelationshipProperty):
            raise Exception(
                'Given attribute is not a relationship property.'
            )

        if property_.secondary is not None:
            return ManyToManyFetcher(self, property_)
        else:
            if property_.direction.name == 'MANYTOONE':
                return ManyToOneFetcher(self, property_)
            else:
                return OneToManyFetcher(self, property_)

    def __call__(self, attr_path):
        if isinstance(attr_path, with_backrefs):
            self.should_populate_backrefs = True
            attr_path = attr_path.attr_path
        else:
            self.should_populate_backrefs = False

        attr = self.parse_attr_path(attr_path, self.should_populate_backrefs)
        if not attr:
            return

        fetcher = self.fetcher(attr.property)
        fetcher.fetch()
        fetcher.populate()


class Fetcher(object):
    def __init__(self, coordinator, property_):
        self.coordinator = coordinator
        self.prop = property_
        self.model = self.prop.mapper.class_
        self.entities = coordinator.entities
        self.first = self.entities[0]
        self.session = object_session(self.first)
        self.init_parent_dict()

    def init_parent_dict(self):
        self.parent_dict = dict(
            (self.local_values(entity), [])
            for entity in self.entities
        )

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

        if self.coordinator.should_populate_backrefs:
            self.populate_backrefs(self.related_entities)


class ManyToManyFetcher(Fetcher):
    def fetch(self):
        column_name = None
        for column in self.prop.remote_side:
            for fk in column.foreign_keys:
                # TODO: make this support inherited tables
                if fk.column.table == self.first.__class__.__table__:
                    column_name = fk.parent.name
                    break
            if column_name:
                break

        self.related_entities = (
            self.session
            .query(self.model, getattr(self.prop.secondary.c, column_name))
            .join(
                self.prop.secondary, self.prop.secondaryjoin
            )
            .filter(
                getattr(self.prop.secondary.c, column_name).in_(
                    self.local_values_list
                )
            )
        )
        for entity, parent_id in self.related_entities:
            self.parent_dict[parent_id].append(
                entity
            )


class ManyToOneFetcher(Fetcher):
    def init_parent_dict(self):
        self.parent_dict = dict(
            (self.local_values(entity), None)
            for entity in self.entities
        )

    def fetch(self):
        column_name = list(self.prop.remote_side)[0].name

        self.related_entities = (
            self.session.query(self.model)
            .filter(
                getattr(self.model, column_name).in_(self.local_values_list)
            )
        )

        for entity in self.related_entities:
            self.parent_dict[getattr(entity, column_name)] = entity


class OneToManyFetcher(Fetcher):
    def fetch(self):
        column_name = list(self.prop.remote_side)[0].name

        self.related_entities = (
            self.session.query(self.model)
            .filter(
                getattr(self.model, column_name).in_(self.local_values_list)
            )
        )

        for entity in self.related_entities:
            self.parent_dict[getattr(entity, column_name)].append(
                entity
            )
