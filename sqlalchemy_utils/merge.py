import six
import sqlalchemy as sa
from sqlalchemy.engine import reflection
from sqlalchemy.orm import object_session, mapperlib


def dependent_foreign_keys(model_class):
    """
    Returns dependent foreign keys as dicts for given model class.

    ** Experimental function **
    """
    session = object_session(model_class)

    engine = session.bind
    inspector = reflection.Inspector.from_engine(engine)
    table_names = inspector.get_table_names()

    dependent_foreign_keys = {}

    for table_name in table_names:
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            dependent_foreign_keys[table_name] = []
            for fk in fks:
                if fk['referred_table'] == model_class.__tablename__:
                    dependent_foreign_keys[table_name].append(fk)
    return dependent_foreign_keys


class Merger(object):
    def memory_merge(self, session, table_name, old_values, new_values):
        # try to fetch mappers for given table and update in memory objects as
        # well as database table
        found = False
        for mapper in mapperlib._mapper_registry:
            class_ = mapper.class_
            if table_name == class_.__table__.name:
                try:
                    (
                        session.query(mapper.class_)
                        .filter_by(**old_values)
                        .update(
                            new_values,
                            'fetch'
                        )
                    )
                except sa.exc.IntegrityError:
                    pass
                found = True
        return found

    def raw_merge(self, session, table, old_values, new_values):
        conditions = []
        for key, value in six.iteritems(old_values):
            conditions.append(getattr(table.c, key) == value)
        sql = (
            table
            .update()
            .where(sa.and_(
                *conditions
            ))
            .values(
                new_values
            )
        )
        try:
            session.execute(sql)
        except sa.exc.IntegrityError:
            pass

    def merge_update(self, table_name, from_, to, foreign_key):
        session = object_session(from_)
        constrained_columns = foreign_key['constrained_columns']
        referred_columns = foreign_key['referred_columns']
        metadata = from_.metadata
        table = metadata.tables[table_name]

        new_values = {}
        for index, column in enumerate(constrained_columns):
            new_values[column] = getattr(
                to, referred_columns[index]
            )

        old_values = {}
        for index, column in enumerate(constrained_columns):
            old_values[column] = getattr(
                from_, referred_columns[index]
            )

        if not self.memory_merge(session, table_name, old_values, new_values):
            self.raw_merge(session, table, old_values, new_values)

    def __call__(self, from_, to):
        """
        Merges entity into another entity. After merging deletes the from_
        argument entity.
        """
        if from_.__tablename__ != to.__tablename__:
            raise Exception()

        session = object_session(from_)
        foreign_keys = dependent_foreign_keys(from_)

        for table_name in foreign_keys:
            for foreign_key in foreign_keys[table_name]:
                self.merge_update(table_name, from_, to, foreign_key)

        session.delete(from_)


def merge(from_, to, merger=Merger):
    """
    Merges entity into another entity. After merging deletes the from_ argument
    entity.

    After merging the from_ entity is deleted from database.

    :param from_: an entity to merge into another entity
    :param to: an entity to merge another entity into
    :param merger: Merger class, by default this is sqlalchemy_utils.Merger
        class
    """
    return Merger()(from_, to)
