import six
from sqlalchemy import types
from sqlalchemy_utils.primitives import NumberRange
from .scalar_coercible import ScalarCoercible


class NumberRangeRawType(types.UserDefinedType):
    """
    Raw number range type, only supports PostgreSQL for now.
    """
    def get_col_spec(self):
        return 'int4range'


class NumberRangeType(types.TypeDecorator, ScalarCoercible):
    """
    NumberRangeType provides way for saving range of numbers into database.

    Example ::


        from sqlalchemy_utils import NumberRangeType, NumberRange


        class Event(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(255))
            estimated_number_of_persons = sa.Column(NumberRangeType)


        party = Event(name=u'party')

        # we estimate the party to contain minium of 10 persons and at max
        # 100 persons
        party.estimated_number_of_persons = NumberRange(10, 100)

        print party.estimated_number_of_persons
        # '10-100'


    NumberRange supports some arithmetic operators:
    ::


        meeting = Event(name=u'meeting')

        meeting.estimated_number_of_persons = NumberRange(20, 40)

        total = (
            meeting.estimated_number_of_persons +
            party.estimated_number_of_persons
        )
        print total
        # '30-140'
    """

    impl = NumberRangeRawType

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value.normalized
        return value

    def process_result_value(self, value, dialect):
        if value:
            return NumberRange(value)
        return value

    def _coerce(self, value):
        if value is not None and not isinstance(value, NumberRange):
            if (
                isinstance(value, six.string_types) or
                isinstance(value, six.integer_types)
            ):
                value = NumberRange(value)
            else:
                raise TypeError('Could not coerce value to NumberRange.')
        return value
