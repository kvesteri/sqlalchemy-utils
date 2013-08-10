import six
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.orm.session import object_session


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


        clubs = session.query(Club).limit(20).all()

        batch_fetch(
            clubs,
            'teams',
            'teams.players',
            'teams.players.user_groups -pb'
        )

    """

    if entities:
        first = entities[0]
        parent_ids = [entity.id for entity in entities]

        for attr_path in attr_paths:
            parent_dict = dict((entity.id, []) for entity in entities)
            populate_backrefs = False

            if isinstance(attr_path, six.string_types):
                attrs = attr_path.split('.')

                if len(attrs) > 1:
                    related_entities = []
                    for entity in entities:
                        related_entities.extend(getattr(entity, attrs[0]))

                    batch_fetch(
                        related_entities,
                        '.'.join(attrs[1:])
                    )
                    continue
                else:
                    args = attrs[-1].split(' ')
                    if '-pb' in args:
                        populate_backrefs = True

                    attr = getattr(
                        first.__class__, args[0]
                    )
            else:
                attr = attr_path

            prop = attr.property
            if not isinstance(prop, RelationshipProperty):
                raise Exception(
                    'Given attribute is not a relationship property.'
                )

            model = prop.mapper.class_

            session = object_session(first)

            if prop.secondary is None:
                if len(prop.remote_side) > 1:
                    raise Exception(
                        'Only relationships with single remote side columns '
                        'are supported.'
                    )

                column_name = list(prop.remote_side)[0].name

                related_entities = (
                    session.query(model)
                    .filter(
                        getattr(model, column_name).in_(parent_ids)
                    )
                )

                for entity in related_entities:
                    parent_dict[getattr(entity, column_name)].append(
                        entity
                    )

            else:
                column_name = None
                for column in prop.remote_side:
                    for fk in column.foreign_keys:
                        # TODO: make this support inherited tables
                        if fk.column.table == first.__class__.__table__:
                            column_name = fk.parent.name
                            break
                    if column_name:
                        break

                related_entities = (
                    session
                    .query(model, getattr(prop.secondary.c, column_name))
                    .join(
                        prop.secondary, prop.secondaryjoin
                    )
                    .filter(
                        getattr(prop.secondary.c, column_name).in_(
                            parent_ids
                        )
                    )
                )
                for entity, parent_id in related_entities:
                    parent_dict[parent_id].append(
                        entity
                    )

            for entity in entities:
                set_committed_value(
                    entity, prop.key, parent_dict[entity.id]
                )
            if populate_backrefs:
                backref_dict = dict(
                    (entity.id, []) for entity, parent_id in related_entities
                )
                for entity, parent_id in related_entities:
                    backref_dict[entity.id].append(
                        session.query(first.__class__).get(parent_id)
                    )
                for entity, parent_id in related_entities:
                    set_committed_value(
                        entity, prop.back_populates, backref_dict[entity.id]
                    )
