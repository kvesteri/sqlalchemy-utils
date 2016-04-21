import pytest
import six
import sqlalchemy as sa

from sqlalchemy_utils import PhoneNumber, PhoneNumberType, types  # noqa


@pytest.fixture
def valid_phone_numbers():
    return [
        '040 1234567',
        '+358 401234567',
        '09 2501234',
        '+358 92501234',
        '0800 939393',
        '09 4243 0456',
        '0600 900 500'
    ]


@pytest.fixture
def invalid_phone_numbers():
    return [
        'abc',
        '+040 1234567',
        '0111234567',
        '358'
    ]


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        phone_number = sa.Column(PhoneNumberType())
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.fixture
def phone_number():
    return PhoneNumber(
        '040 1234567',
        'FI'
    )


@pytest.fixture
def user(session, User, phone_number):
    user = User()
    user.name = u'Someone'
    user.phone_number = phone_number
    session.add(user)
    session.commit()
    return user


@pytest.mark.skipif('types.phone_number.phonenumbers is None')
class TestPhoneNumber(object):

    def test_valid_phone_numbers(self, valid_phone_numbers):
        for raw_number in valid_phone_numbers:
            number = PhoneNumber(raw_number, 'FI')
            assert number.is_valid_number()

    def test_invalid_phone_numbers(self, invalid_phone_numbers):
        for raw_number in invalid_phone_numbers:
            try:
                number = PhoneNumber(raw_number, 'FI')
                assert not number.is_valid_number()
            except:
                pass

    def test_phone_number_attributes(self):
        number = PhoneNumber('+358401234567')
        assert number.e164 == u'+358401234567'
        assert number.international == u'+358 40 1234567'
        assert number.national == u'040 1234567'

    def test_phone_number_str_repr(self):
        number = PhoneNumber('+358401234567')
        if six.PY2:
            assert unicode(number) == number.national  # noqa
            assert str(number) == number.national.encode('utf-8')
        else:
            assert str(number) == number.national


@pytest.mark.skipif('types.phone_number.phonenumbers is None')
class TestPhoneNumberType(object):

    def test_query_returns_phone_number_object(
        self,
        session,
        User,
        user,
        phone_number
    ):
        queried_user = session.query(User).first()
        assert queried_user.phone_number == phone_number

    def test_phone_number_is_stored_as_string(self, session, user):
        result = session.execute(
            'SELECT phone_number FROM "user" WHERE id=:param',
            {'param': user.id}
        )
        assert result.first()[0] == u'+358401234567'

    def test_phone_number_with_extension(self, session, User):
        user = User(phone_number='555-555-5555 Ext. 555')

        session.add(user)
        session.commit()
        session.refresh(user)
        assert user.phone_number.extension == '555'

    def test_empty_phone_number_is_equiv_to_none(self, session, User):
        user = User(phone_number='')

        session.add(user)
        session.commit()
        session.refresh(user)
        assert user.phone_number is None

    @pytest.mark.usefixtures('user')
    def test_phone_number_is_none(self, session, User):
        phone_number = None
        user = User()
        user.name = u'Someone'
        user.phone_number = phone_number
        session.add(user)
        session.commit()
        queried_user = session.query(User)[1]
        assert queried_user.phone_number is None
        result = session.execute(
            'SELECT phone_number FROM "user" WHERE id=:param',
            {'param': user.id}
        )
        assert result.first()[0] is None

    def test_scalar_attributes_get_coerced_to_objects(self, User):
        user = User(phone_number='050111222')

        assert isinstance(user.phone_number, PhoneNumber)


@pytest.mark.skipif('types.phone_number.phonenumbers is None')
class TestPhoneNumberComposite(object):
    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.String(255))
            _phone_number = sa.Column(sa.String(255))
            country = sa.Column(sa.String(255))
            phone_number = sa.orm.composite(
                PhoneNumber,
                _phone_number,
                country
            )
        return User

    @pytest.fixture
    def user(self, session, User):
        user = User()
        user.name = u'Someone'
        user.phone_number = PhoneNumber('+35840111222', 'FI')
        session.add(user)
        session.commit()
        return user

    def test_query_returns_phone_number_object(
        self,
        session,
        User,
        user
    ):
        queried_user = session.query(User).first()
        assert queried_user.phone_number.national == '040 111222'
        assert queried_user.phone_number.region == 'FI'
