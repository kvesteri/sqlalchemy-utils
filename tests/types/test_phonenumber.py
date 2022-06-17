import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from sqlalchemy_utils import (  # noqa
    PhoneNumber,
    PhoneNumberParseException,
    PhoneNumberType,
    types
)
from sqlalchemy_utils.compat import _select_args

VALID_PHONE_NUMBERS = (
    "040 1234567",
    "+358 401234567",
    "09 2501234",
    "+358 92501234",
    "0800 939393",
    "09 4243 0456",
    "0600 900 500",
)


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = "user"
        id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        phone_number = sa.Column(PhoneNumberType())

    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.fixture
def phone_number():
    return PhoneNumber("040 1234567", "FI")


@pytest.fixture
def user(session, User, phone_number):
    user = User()
    user.name = "Someone"
    user.phone_number = phone_number
    session.add(user)
    session.commit()
    return user


@pytest.mark.skipif("types.phone_number.phonenumbers is None")
class TestPhoneNumber:
    @pytest.mark.parametrize("raw_number", VALID_PHONE_NUMBERS)
    def test_valid_phone_numbers(self, raw_number):
        number = PhoneNumber(raw_number, "FI")
        assert number.is_valid_number()

    @pytest.mark.parametrize("raw_number", ("abc", "+040 1234567"))
    def test_invalid_phone_numbers__constructor_fails(self, raw_number):
        with pytest.raises(PhoneNumberParseException):
            PhoneNumber(raw_number, "FI")

    @pytest.mark.parametrize("raw_number", ("0111234567", "358"))
    def test_invalid_phone_numbers__is_valid_number(self, raw_number):
        number = PhoneNumber(raw_number, "FI")
        assert not number.is_valid_number()

    def test_invalid_phone_numbers_throw_dont_wrap_exception(self, session, User):
        with pytest.raises(PhoneNumberParseException):
            session.execute(
                User.__table__.insert().values(name="Someone", phone_number="abc")
            )

    def test_phone_number_attributes(self):
        number = PhoneNumber("+358401234567")
        assert number.e164 == "+358401234567"
        assert number.international == "+358 40 1234567"
        assert number.national == "040 1234567"

    def test_phone_number_attributes_for_short_code(self):
        """
        For international and national shortcode remains the same, if we pass
        short code to PhoneNumber library without giving check_region it will
        raise exception
        :return:
        """
        number = PhoneNumber("72404", check_region=False)
        assert number.e164 == "+072404"
        assert number.international == "72404"
        assert number.national == "72404"

    def test_phone_number_str_repr(self):
        number = PhoneNumber("+358401234567")
        assert str(number) == number.national

    def test_phone_number_hash(self):
        number1 = PhoneNumber("+821023456789")
        number2 = PhoneNumber("+82 10-2345-6789")
        assert hash(number1) == hash(number2)
        assert hash(number1) == hash(number1.e164)
        assert {number1} == {number2}


@pytest.mark.skipif("types.phone_number.phonenumbers is None")
class TestPhoneNumberType:
    def test_query_returns_phone_number_object(self, session, User, user, phone_number):
        queried_user = session.query(User).first()
        assert queried_user.phone_number == phone_number

    def test_phone_number_is_stored_as_string(self, session, user):
        result = session.execute(
            sa.text('SELECT phone_number FROM "user" WHERE id=:param'),
            {"param": user.id},
        )
        assert result.first()[0] == "+358401234567"

    def test_phone_number_with_extension(self, session, User):
        user = User(phone_number="555-555-5555 Ext. 555")

        session.add(user)
        session.commit()
        session.refresh(user)
        assert user.phone_number.extension == "555"

    def test_empty_phone_number_is_equiv_to_none(self, session, User):
        user = User(phone_number="")

        session.add(user)
        session.commit()
        session.refresh(user)
        assert user.phone_number is None

    def test_uses_phonenumber_class_as_python_type(self):
        assert PhoneNumberType().python_type is PhoneNumber

    @pytest.mark.usefixtures("user")
    def test_phone_number_is_none(self, session, User):
        phone_number = None
        user = User()
        user.name = "Someone"
        user.phone_number = phone_number
        session.add(user)
        session.commit()
        queried_user = session.query(User)[1]
        assert queried_user.phone_number is None
        result = session.execute(
            sa.text('SELECT phone_number FROM "user" WHERE id=:param'),
            {"param": user.id},
        )
        assert result.first()[0] is None

    def test_scalar_attributes_get_coerced_to_objects(self, User):
        user = User(phone_number="050111222")

        assert isinstance(user.phone_number, PhoneNumber)

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.phone_number))
        # the type should be cacheable and not throw exception
        session.execute(query)


@pytest.mark.skipif("types.phone_number.phonenumbers is None")
class TestPhoneNumberComposite:
    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = "user"
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.String(255))
            _phone_number = sa.Column(sa.String(255))
            country = sa.Column(sa.String(255))
            phone_number = sa.orm.composite(PhoneNumber, _phone_number, country)

        return User

    @pytest.fixture
    def user(self, session, User):
        user = User()
        user.name = "Someone"
        user.phone_number = PhoneNumber("+35840111222", "FI")
        session.add(user)
        session.commit()
        return user

    def test_query_returns_phone_number_object(self, session, User, user):
        queried_user = session.query(User).first()
        assert queried_user.phone_number.national == "040 111222"
        assert queried_user.phone_number.region == "FI"
