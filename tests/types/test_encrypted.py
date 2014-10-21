import sqlalchemy as sa
from pytest import mark
cryptography = None
try:
    import cryptography
except ImportError:
    pass

from tests import TestCase
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted import AesEngine, FernetEngine


@mark.skipif('cryptography is None')
class EncryptedTypeTestCase(TestCase):
    def setup_method(self, method):
        # set some test values
        self.test_key = 'secretkey1234'
        self.user_name = u'someone'
        self.test_token = self.generate_test_token()
        self.active = True
        self.accounts_num = 2
        self.searched_user = None
        super(EncryptedTypeTestCase, self).setup_method(method)
        # set the values to the user object
        self.user = self.User()
        self.user.username = self.user_name
        self.user.access_token = self.test_token
        self.user.is_active = self.active
        self.user.accounts_num = self.accounts_num
        self.session.add(self.user)
        self.session.commit()

    def teardown_method(self, method):
        self.session.delete(self.user)
        self.session.commit()
        del self.user_name
        del self.test_token
        del self.active
        del self.accounts_num
        del self.test_key
        del self.searched_user
        super(EncryptedTypeTestCase, self).teardown_method(method)

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            username = sa.Column(EncryptedType(
                sa.Unicode,
                self.test_key,
                self.__class__.encryption_engine))
            access_token = sa.Column(EncryptedType(
                sa.String,
                self.test_key,
                self.__class__.encryption_engine))
            is_active = sa.Column(EncryptedType(
                sa.Boolean,
                self.test_key,
                self.__class__.encryption_engine))
            accounts_num = sa.Column(EncryptedType(
                sa.Integer,
                self.test_key,
                self.__class__.encryption_engine))

            def __repr__(self):
                return (
                    "User(id={}, username={}, access_token={},"
                    "active={}, accounts={})".format(
                        self.id,
                        self.username,
                        self.access_token,
                        self.is_active,
                        self.accounts_num
                    )
                )

        self.User = User

    def assert_username(self, _user):
        assert _user.username == self.user_name

    def assert_access_token(self, _user):
        assert _user.access_token == self.test_token

    def assert_is_active(self, _user):
        assert _user.is_active == self.active

    def assert_accounts_num(self, _user):
        assert _user.accounts_num == self.accounts_num

    def generate_test_token(self):
        import string
        import random
        token = ""
        characters = string.ascii_letters + string.digits
        for i in range(60):
            token += ''.join(random.choice(characters))
        return token


class TestAesEncryptedTypeTestcase(EncryptedTypeTestCase):

    encryption_engine = AesEngine

    def test_unicode(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.access_token == self.test_token
        ).first()
        self.assert_username(self.searched_user)

    def test_string(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.username == self.user_name
        ).first()
        self.assert_access_token(self.searched_user)

    def test_boolean(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.access_token == self.test_token
        ).first()
        self.assert_is_active(self.searched_user)

    def test_integer(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.access_token == self.test_token
        ).first()
        self.assert_accounts_num(self.searched_user)


class TestFernetEnryptedTypeTestCase(EncryptedTypeTestCase):

    encryption_engine = FernetEngine

    def test_unicode(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.id == self.user.id
        ).first()
        self.assert_username(self.searched_user)

    def test_string(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.id == self.user.id
        ).first()
        self.assert_access_token(self.searched_user)

    def test_boolean(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.id == self.user.id
        ).first()
        self.assert_is_active(self.searched_user)

    def test_integer(self):
        self.searched_user = self.session.query(self.User).filter(
            self.User.id == self.user.id
        ).first()
        self.assert_accounts_num(self.searched_user)
