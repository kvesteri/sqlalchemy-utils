import six
from sqlalchemy import types
from sqlalchemy_utils import ImproperlyConfigured
from .scalar_coercible import ScalarCoercible


try:
    import phonenumbers
    from phonenumbers.phonenumber import PhoneNumber as BasePhoneNumber

except ImportError:
    phonenumbers = None
    BasePhoneNumber = object


class PhoneNumber(BasePhoneNumber):
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
        # Bail if phonenumbers is not found.
        if phonenumbers is None:
            raise ImproperlyConfigured(
                "'phonenumbers' is required to use 'PhoneNumber'")

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

    def __unicode__(self):
        return self.national

    def __str__(self):
        return six.text_type(self.national).encode('utf-8')


class PhoneNumberType(types.TypeDecorator, ScalarCoercible):
    """
    Changes PhoneNumber objects to a string representation on the way in and
    changes them back to PhoneNumber objects on the way out. If E164 is used
    as storing format, no country code is needed for parsing the database
    value to PhoneNumber object.

    ::

        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            phone_number = sa.Column(PhoneNumberType())


        user = User(phone_number='+358401234567')

        user.phone_number.e164  # u'+358401234567'
        user.phone_number.international  # u'+358 40 1234567'
        user.phone_number.national  # u'040 1234567'
    """
    STORE_FORMAT = 'e164'
    impl = types.Unicode(20)

    def __init__(self, country_code='US', max_length=20, *args, **kwargs):
        # Bail if phonenumbers is not found.
        if phonenumbers is None:
            raise ImproperlyConfigured(
                "'phonenumbers' is required to use 'PhoneNumberType'")

        super(PhoneNumberType, self).__init__(*args, **kwargs)
        self.country_code = country_code
        self.impl = types.Unicode(max_length)

    def process_bind_param(self, value, dialect):
        if value:
            return getattr(value, self.STORE_FORMAT)
        return value

    def process_result_value(self, value, dialect):
        if value:
            return PhoneNumber(value, self.country_code)
        return value

    def _coerce(self, value):
        if value is not None and not isinstance(value, PhoneNumber):
            value = PhoneNumber(value, country_code=self.country_code)
        return value
