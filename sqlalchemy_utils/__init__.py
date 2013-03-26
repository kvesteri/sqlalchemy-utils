import phonenumbers
from functools import wraps
import sqlalchemy as sa
from sqlalchemy.engine import reflection
from sqlalchemy.orm import defer, object_session, mapperlib
from sqlalchemy.orm.collections import InstrumentedList as _InstrumentedList
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.orm.query import _ColumnEntity
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.sql.expression import desc, asc
from sqlalchemy import types


class PhoneNumber(phonenumbers.phonenumber.PhoneNumber):
    '''
    Extends a PhoneNumber class from `Python phonenumbers library`_. Adds
    different phone number formats to attributes, so they can be easily used
    in templates. Phone number validation method is also implemented.

    Takes the raw phone number and country code as params and parses them
    into a PhoneNumber object.

    .. _Python phonenumbers library:
       https://github.com/daviddrysdale/python-phonenumbers

    :param raw_number:
        String representation of the phone number.
    :param country_code:
        Country code of the phone number.
    '''
    def __init__(self, raw_number, country_code=None):
        self._phone_number = phonenumbers.parse(raw_number, country_code)
        super(PhoneNumber, self).__init__(
            country_code=self._phone_number.country_code,
            national_number=self._phone_number.national_number,
            extension=self._phone_number.extension,
            italian_leading_zero=self._phone_number.italian_leading_zero,
            raw_input=self._phone_number.raw_input,
            country_code_source=self._phone_number.country_code_source,
            preferred_domestic_carrier_code=
            self._phone_number.preferred_domestic_carrier_code
        )
        self.national = phonenumbers.format_number(
            self._phone_number,
            phonenumbers.PhoneNumberFormat.NATIONAL
        )
        self.international = phonenumbers.format_number(
            self._phone_number,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        self.e164 = phonenumbers.format_number(
            self._phone_number,
            phonenumbers.PhoneNumberFormat.E164
        )

    def is_valid_number(self):
        return phonenumbers.is_valid_number(self._phone_number)


class PhoneNumberType(types.TypeDecorator):
    """
    Changes PhoneNumber objects to a string representation on the way in and
    changes them back to PhoneNumber objects on the way out. If E164 is used
    as storing format, no country code is needed for parsing the database
    value to PhoneNumber object.
    """
    STORE_FORMAT = 'e164'
    impl = types.Unicode(20)

    def __init__(self, country_code='US', max_length=20, *args, **kwargs):
        super(PhoneNumberType, self).__init__(*args, **kwargs)
        self.country_code = country_code
        self.impl = types.Unicode(max_length)

    def process_bind_param(self, value, dialect):
        return getattr(value, self.STORE_FORMAT)

    def process_result_value(self, value, dialect):
        return PhoneNumber(value, self.country_code)


class InstrumentedList(_InstrumentedList):
    """Enhanced version of SQLAlchemy InstrumentedList. Provides some
    additional functionality."""

    def any(self, attr):
        return any(getattr(item, attr) for item in self)

    def all(self, attr):
        return all(getattr(item, attr) for item in self)


def instrumented_list(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return InstrumentedList([item for item in f(*args, **kwargs)])
    return wrapper


def sort_query(query, sort):
    """
    Applies an sql ORDER BY for given query. This function can be easily used
    with user-defined sorting.

    The examples use the following model definition:

        >>> import sqlalchemy as sa
        >>> from sqlalchemy import create_engine
        >>> from sqlalchemy.orm import sessionmaker
        >>> from sqlalchemy.ext.declarative import declarative_base
        >>> from sqlalchemy_utils import sort_query
        >>>
        >>>
        >>> engine = create_engine(
        ...     'sqlite:///'
        ... )
        >>> Base = declarative_base()
        >>> Session = sessionmaker(bind=engine)
        >>> session = Session()
        >>>
        >>> class Category(Base):
        ...     __tablename__ = 'category'
        ...     id = sa.Column(sa.Integer, primary_key=True)
        ...     name = sa.Column(sa.Unicode(255))
        >>>
        >>> class Article(Base):
        ...     __tablename__ = 'article'
        ...     id = sa.Column(sa.Integer, primary_key=True)
        ...     name = sa.Column(sa.Unicode(255))
        ...     category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))
        ...
        ...     category = sa.orm.relationship(
        ...         Category, primaryjoin=category_id == Category.id
        ...     )



    1. Applying simple ascending sort

        >>> query = session.query(Article)
        >>> query = sort_query(query, 'name')

    2. Appying descending sort

        >>> query = sort_query(query, '-name')

    3. Applying sort to custom calculated label

        >>> query = session.query(
        ...     Category, db.func.count(Article.id).label('articles')
        ... )
        >>> query = sort_query(query, 'articles')

    4. Applying sort to joined table column

        >>> query = session.query(Article).join(Article.category)
        >>> query = sort_query(query, 'category-name')


    :param query: query to be modified
    :param sort: string that defines the label or column to sort the query by
    :param errors: whether or not to raise exceptions if unknown sort column
                   is passed
    """
    entities = [entity.entity_zero.class_ for entity in query._entities]
    for mapper in query._join_entities:
        if isinstance(mapper, Mapper):
            entities.append(mapper.class_)
        else:
            entities.append(mapper)

    # get all label names for queries such as:
    # db.session.query(Category, db.func.count(Article.id).label('articles'))
    labels = []
    for entity in query._entities:
        if isinstance(entity, _ColumnEntity) and entity._label_name:
            labels.append(entity._label_name)

    if not sort:
        return query

    if sort[0] == '-':
        func = desc
        sort = sort[1:]
    else:
        func = asc

    component = None
    parts = sort.split('-')
    if len(parts) > 1:
        component = parts[0]
        sort = parts[1]
    if sort in labels:
        return query.order_by(func(sort))

    for entity in entities:
        table = entity.__table__
        if component and table.name != component:
            continue
        if sort in table.columns:
            try:
                attr = getattr(entity, sort)
                query = query.order_by(func(attr))
            except AttributeError:
                pass
            break
    return query


def defer_except(query, columns):
    """
    Deferred loads all columns in given query, except the ones given.

    This function is very useful when working with models with myriad of
    columns and you want to deferred load many columns.

        >>> from sqlalchemy_utils import defer_except
        >>> query = session.query(Article)
        >>> query = defer_except(Article, [Article.id, Article.name])

    :param columns: columns not to deferred load
    """
    model = query._entities[0].entity_zero.class_
    fields = set(model._sa_class_manager.values())
    for field in fields:
        property_ = field.property
        if isinstance(property_, ColumnProperty):
            column = property_.columns[0]
            if column.name not in columns:
                query = query.options(defer(property_.key))
    return query


def escape_like(string, escape_char='*'):
    """
    Escapes the string paremeter used in SQL LIKE expressions

        >>> from sqlalchemy_utils import escape_like
        >>> query = session.query(User).filter(
        ...     User.name.ilike(escape_like('John'))
        ... )


    :param string: a string to escape
    :param escape_char: escape character
    """
    return (
        string
        .replace(escape_char, escape_char * 2)
        .replace('%', escape_char + '%')
        .replace('_', escape_char + '_')
    )


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
        for key, value in old_values.items():
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
