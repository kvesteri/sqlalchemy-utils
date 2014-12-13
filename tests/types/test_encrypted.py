import sqlalchemy as sa
from datetime import datetime, date, time
import pytest
from pytest import mark
cryptography = None
try:
    import cryptography
except ImportError:
    pass

from tests import TestCase
from sqlalchemy_utils import EncryptedType, PhoneNumberType, ColorType
from sqlalchemy_utils.types.encrypted import AesEngine, FernetEngine


@mark.skipif('cryptography is None')
class EncryptedTypeTestCase(TestCase):

    @pytest.fixture(scope='function')
    def user(self, request):
        # set the values to the user object
        self.user = self.User()
        self.user.username = self.user_name
        self.user.phone = self.user_phone
        self.user.color = self.user_color
        self.user.date = self.user_date
        self.user.time = self.user_time
        self.user.enum = self.user_enum
        self.user.datetime = self.user_datetime
        self.user.access_token = self.test_token
        self.user.is_active = self.active
        self.user.accounts_num = self.accounts_num
        self.session.add(self.user)
        self.session.commit()

        # register a finalizer to cleanup
        def finalize():
            del self.user_name
            del self.test_token
            del self.active
            del self.accounts_num
            del self.test_key
            del self.searched_user

        request.addfinalizer(finalize)

        return self.session.query(self.User).get(self.user.id)

    def generate_test_token(self):
        import string
        import random
        token = ''
        characters = string.ascii_letters + string.digits
        for i in range(60):
            token += ''.join(random.choice(characters))
        return token

    def create_models(self):
        # set some test values
        self.test_key = 'secretkey1234'
        self.user_name = u'someone'
        self.user_phone = u'(555) 555-5555'
        self.user_color = u'#fff'
        self.user_enum = 'One'
        self.user_date = date(2010, 10, 2)
        self.user_time = time(10, 12)
        self.user_datetime = datetime(2010, 10, 2, 10, 12)
        self.test_token = self.generate_test_token()
        self.active = True
        self.accounts_num = 2
        self.searched_user = None

        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)

            username = sa.Column(EncryptedType(
                sa.Unicode,
                self.test_key,
                self.__class__.encryption_engine)
            )

            access_token = sa.Column(EncryptedType(
                sa.String,
                self.test_key,
                self.__class__.encryption_engine)
            )

            is_active = sa.Column(EncryptedType(
                sa.Boolean,
                self.test_key,
                self.__class__.encryption_engine)
            )

            accounts_num = sa.Column(EncryptedType(
                sa.Integer,
                self.test_key,
                self.__class__.encryption_engine)
            )

            phone = sa.Column(EncryptedType(
                PhoneNumberType,
                self.test_key,
                self.__class__.encryption_engine)
            )

            color = sa.Column(EncryptedType(
                ColorType,
                self.test_key,
                self.__class__.encryption_engine)
            )

            date = sa.Column(EncryptedType(
                sa.Date,
                self.test_key,
                self.__class__.encryption_engine)
            )

            time = sa.Column(EncryptedType(
                sa.Time,
                self.test_key,
                self.__class__.encryption_engine)
            )

            datetime = sa.Column(EncryptedType(
                sa.DateTime,
                self.test_key,
                self.__class__.encryption_engine)
            )

            enum = sa.Column(EncryptedType(
                sa.Enum('One', name='user_enum_t'),
                self.test_key,
                self.__class__.encryption_engine)
            )

        self.User = User

        class Team(self.Base):
            __tablename__ = 'team'
            id = sa.Column(sa.Integer, primary_key=True)
            key = sa.Column(sa.String(50))
            name = sa.Column(EncryptedType(
                sa.Unicode,
                lambda: self._team_key,
                self.__class__.encryption_engine)
            )

        self.Team = Team

    def test_unicode(self, user):
        assert user.username == self.user_name

    def test_string(self, user):
        assert user.access_token == self.test_token

    def test_boolean(self, user):
        assert user.is_active == self.active

    def test_integer(self, user):
        assert user.accounts_num == self.accounts_num

    def test_phone_number(self, user):
        assert str(user.phone) == self.user_phone

    def test_color(self, user):
        assert user.color.hex == self.user_color

    def test_date(self, user):
        assert user.date == self.user_date

    def test_datetime(self, user):
        assert user.datetime == self.user_datetime

    def test_time(self, user):
        assert user.time == self.user_time

    def test_enum(self, user):
        assert user.enum == self.user_enum

    def test_lookup_key(self):
        # Add teams
        self._team_key = 'one'
        team = self.Team(key=self._team_key, name=u'One')
        self.session.add(team)
        self.session.commit()
        team_1_id = team.id

        self._team_key = 'two'
        team = self.Team(key=self._team_key)
        team.name = u'Two'
        self.session.add(team)
        self.session.commit()
        team_2_id = team.id

        # Lookup teams
        self._team_key = self.session.query(self.Team.key).filter_by(
            id=team_1_id
        ).one()[0]

        team = self.session.query(self.Team).get(team_1_id)

        assert team.name == u'One'

        with pytest.raises(Exception):
            self.session.query(self.Team).get(team_2_id)

        self.session.expunge_all()

        self._team_key = self.session.query(self.Team.key).filter_by(
            id=team_2_id
        ).one()[0]

        team = self.session.query(self.Team).get(team_2_id)

        assert team.name == u'Two'

        with pytest.raises(Exception):
            self.session.query(self.Team).get(team_1_id)

        self.session.expunge_all()

        # Remove teams
        self.session.query(self.Team).delete()
        self.session.commit()


class TestAesEncryptedTypeTestcase(EncryptedTypeTestCase):

    encryption_engine = AesEngine

    def test_lookup_by_encrypted_string(self, user):
        test = self.session.query(self.User).filter(
            self.User.username == self.user_name
        ).first()

        assert test.username == user.username


class TestFernetEncryptedTypeTestCase(EncryptedTypeTestCase):

    encryption_engine = FernetEngine
