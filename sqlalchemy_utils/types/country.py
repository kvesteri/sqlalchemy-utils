from sqlalchemy import types
import six
from .scalar_coercible import ScalarCoercible
from sqlalchemy_utils import i18n


class Country(object):
    def __init__(self, code_or_country):
        if isinstance(code_or_country, Country):
            self.code = code_or_country.code
        else:
            self.code = code_or_country

    @property
    def name(self):
        return i18n.get_locale().territories[self.code]

    def __eq__(self, other):
        if isinstance(other, Country):
            return self.code == other.code
        elif isinstance(other, six.string_types):
            return self.code == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.code)

    def __unicode__(self):
        return self.name


class CountryType(types.TypeDecorator, ScalarCoercible):
    """
    Changes Country objects to a string representation on the way in and
    changes them back to Country objects on the way out.

    In order to use CountryType you need to install Babel_ first.

    .. _Babel: http://babel.pocoo.org/

    ::


        from sqlalchemy_utils import CountryType, Country


        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(255))
            country = sa.Column(CountryType)


        user = User()
        user.country = Country('FI')
        session.add(user)
        session.commit()

        user.country  # Country('FI')
        user.country.name  # Finland

        print user.country  # Finland


    CountryType is scalar coercible::


        user.country = 'US'
        user.country  # Country('US')
    """
    impl = types.String(2)
    python_type = Country

    def process_bind_param(self, value, dialect):
        if isinstance(value, Country):
            return value.code

        if isinstance(value, six.string_types):
            return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return Country(value)

    def _coerce(self, value):
        if value is not None and not isinstance(value, Country):
            return Country(value)
        return value
