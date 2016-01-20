from datetime import date, datetime, time

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import ColorType, EncryptedType, PhoneNumberType
from sqlalchemy_utils.types.encrypted import AesEngine, FernetEngine

cryptography = None
try:
    import cryptography  # noqa
except ImportError:
    pass


@pytest.fixture
def User(Base, encryption_engine, test_key):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)

        username = sa.Column(EncryptedType(
            sa.Unicode,
            test_key,
            encryption_engine)
        )

        access_token = sa.Column(EncryptedType(
            sa.String,
            test_key,
            encryption_engine)
        )

        is_active = sa.Column(EncryptedType(
            sa.Boolean,
            test_key,
            encryption_engine)
        )

        accounts_num = sa.Column(EncryptedType(
            sa.Integer,
            test_key,
            encryption_engine)
        )

        phone = sa.Column(EncryptedType(
            PhoneNumberType,
            test_key,
            encryption_engine)
        )

        color = sa.Column(EncryptedType(
            ColorType,
            test_key,
            encryption_engine)
        )

        date = sa.Column(EncryptedType(
            sa.Date,
            test_key,
            encryption_engine)
        )

        time = sa.Column(EncryptedType(
            sa.Time,
            test_key,
            encryption_engine)
        )

        datetime = sa.Column(EncryptedType(
            sa.DateTime,
            test_key,
            encryption_engine)
        )

        enum = sa.Column(EncryptedType(
            sa.Enum('One', name='user_enum_t'),
            test_key,
            encryption_engine)
        )

    return User


@pytest.fixture
def test_key():
    return 'secretkey1234'


@pytest.fixture
def user_name():
    return u'someone'


@pytest.fixture
def user_phone():
    return u'(555) 555-5555'


@pytest.fixture
def user_color():
    return u'#fff'


@pytest.fixture
def user_enum():
    return 'One'


@pytest.fixture
def user_date():
    return date(2010, 10, 2)


@pytest.fixture
def user_time():
    return time(10, 12)


@pytest.fixture
def user_datetime():
    return datetime(2010, 10, 2, 10, 12)


@pytest.fixture
def test_token():
    import string
    import random
    token = ''
    characters = string.ascii_letters + string.digits
    for i in range(60):
        token += ''.join(random.choice(characters))
    return token


@pytest.fixture
def active():
    return True


@pytest.fixture
def accounts_num():
    return 2


@pytest.fixture
def user(
    request,
    session,
    User,
    user_name,
    user_phone,
    user_color,
    user_date,
    user_time,
    user_enum,
    user_datetime,
    test_token,
    active,
    accounts_num
):
    # set the values to the user object
    user = User()
    user.username = user_name
    user.phone = user_phone
    user.color = user_color
    user.date = user_date
    user.time = user_time
    user.enum = user_enum
    user.datetime = user_datetime
    user.access_token = test_token
    user.is_active = active
    user.accounts_num = accounts_num
    session.add(user)
    session.commit()

    return session.query(User).get(user.id)


@pytest.mark.skipif('cryptography is None')
class EncryptedTypeTestCase(object):

    @pytest.fixture
    def Team(self, Base, encryption_engine):
        self._team_key = None

        class Team(Base):
            __tablename__ = 'team'
            id = sa.Column(sa.Integer, primary_key=True)
            key = sa.Column(sa.String(50))
            name = sa.Column(EncryptedType(
                sa.Unicode,
                lambda: self._team_key,
                encryption_engine)
            )
        return Team

    @pytest.fixture
    def init_models(self, User, Team):
        pass

    def test_unicode(self, user, user_name):
        assert user.username == user_name

    def test_string(self, user, test_token):
        assert user.access_token == test_token

    def test_boolean(self, user, active):
        assert user.is_active == active

    def test_integer(self, user, accounts_num):
        assert user.accounts_num == accounts_num

    def test_phone_number(self, user, user_phone):
        assert str(user.phone) == user_phone

    def test_color(self, user, user_color):
        assert user.color.hex == user_color

    def test_date(self, user, user_date):
        assert user.date == user_date

    def test_datetime(self, user, user_datetime):
        assert user.datetime == user_datetime

    def test_time(self, user, user_time):
        assert user.time == user_time

    def test_enum(self, user, user_enum):
        assert user.enum == user_enum

    def test_lookup_key(self, session, Team):
        # Add teams
        self._team_key = 'one'
        team = Team(key=self._team_key, name=u'One')
        session.add(team)
        session.commit()
        team_1_id = team.id

        self._team_key = 'two'
        team = Team(key=self._team_key)
        team.name = u'Two'
        session.add(team)
        session.commit()
        team_2_id = team.id

        # Lookup teams
        self._team_key = session.query(Team.key).filter_by(
            id=team_1_id
        ).one()[0]

        team = session.query(Team).get(team_1_id)

        assert team.name == u'One'

        with pytest.raises(Exception):
            session.query(Team).get(team_2_id)

        session.expunge_all()

        self._team_key = session.query(Team.key).filter_by(
            id=team_2_id
        ).one()[0]

        team = session.query(Team).get(team_2_id)

        assert team.name == u'Two'

        with pytest.raises(Exception):
            session.query(Team).get(team_1_id)

        session.expunge_all()

        # Remove teams
        session.query(Team).delete()
        session.commit()


class TestAesEncryptedTypeTestcase(EncryptedTypeTestCase):

    @pytest.fixture
    def encryption_engine(self):
        return AesEngine

    def test_lookup_by_encrypted_string(self, session, User, user, user_name):
        test = session.query(User).filter(
            User.username == user_name
        ).first()

        assert test.username == user.username


class TestFernetEncryptedTypeTestCase(EncryptedTypeTestCase):

    @pytest.fixture
    def encryption_engine(self):
        return FernetEngine
