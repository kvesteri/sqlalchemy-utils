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
        fetcher = BatchFetcher(entities)
        for attr_path in attr_paths:
            fetcher(attr_path)


class BatchFetcher(object):
    def __init__(self, entities):
        self.entities = entities
        self.first = entities[0]
        self.parent_ids = [entity.id for entity in entities]
        self.session = object_session(self.first)

    def populate_backrefs(self, related_entities):
        """
        Populates backrefs for given related entities.
        """

        backref_dict = dict(
            (entity.id, []) for entity, parent_id in related_entities
        )
        for entity, parent_id in related_entities:
            backref_dict[entity.id].append(
                self.session.query(self.first.__class__).get(parent_id)
            )
        for entity, parent_id in related_entities:
            set_committed_value(
                entity, self.prop.back_populates, backref_dict[entity.id]
            )

    def populate_entities(self):
        """
        Populate batch fetched entities to parent objects.
        """
        for entity in self.entities:
            set_committed_value(
                entity,
                self.prop.key,
                self.parent_dict[entity.id]
            )

        if self.should_populate_backrefs:
            self.populate_backrefs(self.related_entities)

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

        column_name = list(self.prop.remote_side)[0].name

        self.related_entities = (
            self.session.query(self.model)
            .filter(
                getattr(self.model, column_name).in_(self.parent_ids)
            )
        )

        for entity in self.related_entities:
            self.parent_dict[getattr(entity, column_name)].append(
                entity
            )

    def fetch_association_entities(self):
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
                    self.parent_ids
                )
            )
        )
        for entity, parent_id in self.related_entities:
            self.parent_dict[parent_id].append(
                entity
            )

    def __call__(self, attr_path):
        self.parent_dict = dict(
            (entity.id, []) for entity in self.entities
        )
        if isinstance(attr_path, with_backrefs):
            self.should_populate_backrefs = True
            attr_path = attr_path.attr_path
        else:
            self.should_populate_backrefs = False

        attr = self.parse_attr_path(attr_path, self.should_populate_backrefs)
        if not attr:
            return

        self.prop = attr.property
        if not isinstance(self.prop, RelationshipProperty):
            raise Exception(
                'Given attribute is not a relationship property.'
            )

        self.model = self.prop.mapper.class_

        if self.prop.secondary is None:
            self.fetch_relation_entities()
        else:
            self.fetch_association_entities()
        self.populate_entities()
