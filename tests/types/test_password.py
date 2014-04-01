from pytest import mark
import sqlalchemy as sa
from tests import TestCase
from sqlalchemy import inspect
from sqlalchemy_utils.types import password
from sqlalchemy_utils import Password, PasswordType


@mark.skipif('password.passlib is None')
class TestPasswordType(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            password = sa.Column(PasswordType(
                schemes=[
                    'pbkdf2_sha512',
                    'pbkdf2_sha256',
                    'md5_crypt',
                    'hex_md5'
                ],

                deprecated=['md5_crypt', 'hex_md5']
            ))

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_encrypt(self):
        """Should encrypt the password on setting the attribute."""
        obj = self.User()
        obj.password = b'b'

        assert obj.password.hash != 'b'
        assert obj.password.hash.startswith(b'$pbkdf2-sha512$')

    def test_check(self):
        """
        Should be able to compare the plaintext against the
        encrypted form.
        """
        obj = self.User()
        obj.password = 'b'

        assert obj.password == 'b'
        assert obj.password != 'a'

        self.session.add(obj)
        self.session.commit()

        obj = self.session.query(self.User).get(obj.id)

        assert obj.password == b'b'
        assert obj.password != 'a'

    def test_check_and_update(self):
        """
        Should be able to compare the plaintext against a deprecated
        encrypted form and have it auto-update to the preferred version.
        """

        from passlib.hash import md5_crypt

        obj = self.User()
        obj.password = Password(md5_crypt.encrypt('b'))

        assert obj.password.hash.decode('utf8').startswith('$1$')
        assert obj.password == 'b'
        assert obj.password.hash.decode('utf8').startswith('$pbkdf2-sha512$')

    def test_auto_column_length(self):
        """Should derive the correct column length from the specified schemes.
        """

        from passlib.hash import pbkdf2_sha512

        kind = inspect(self.User).c.password.type

        # name + rounds + salt + hash + ($ * 4) of largest hash
        expected_length = len(pbkdf2_sha512.name)
        expected_length += len(str(pbkdf2_sha512.max_rounds))
        expected_length += pbkdf2_sha512.max_salt_size
        expected_length += pbkdf2_sha512.encoded_checksum_size
        expected_length += 4

        assert kind.length == expected_length

    def test_without_schemes(self):
        assert PasswordType(schemes=[]).length == 1024

    def test_compare(self):
        from passlib.hash import md5_crypt

        obj = self.User()
        obj.password = Password(md5_crypt.encrypt('b'))

        other = self.User()
        other.password = Password(md5_crypt.encrypt('b'))

        # Not sure what to assert here; the test raised an error before.
        assert obj.password != other.password

    def test_set_none(self):

        obj = self.User()
        obj.password = None

        assert obj.password is None

        self.session.add(obj)
        self.session.commit()

        obj = self.session.query(self.User).get(obj.id)

        assert obj.password is None

    def test_update_none(self):
        """
        Should be able to change a password from ``None`` to a valid
        password.
        """

        obj = self.User()
        obj.password = None

        self.session.add(obj)
        self.session.commit()

        obj = self.session.query(self.User).get(obj.id)
        obj.password = 'b'

        self.session.commit()

    def test_compare_none(self):
        """
        Should be able to compare a password of ``None``.
        """

        obj = self.User()
        obj.password = None

        assert obj.password is None
        assert obj.password == None

        obj.password = 'b'

        assert obj.password is not None
        assert obj.password != None

    def test_check_and_update_persist(self):
        """
        When a password is compared, the hash should update if needed to
        change the algorithm; and, commit to the database.
        """

        from passlib.hash import md5_crypt

        obj = self.User()
        obj.password = Password(md5_crypt.encrypt('b'))

        self.session.add(obj)
        self.session.commit()

        assert obj.password.hash.decode('utf8').startswith('$1$')
        assert obj.password == 'b'

        self.session.commit()

        obj = self.session.query(self.User).get(obj.id)

        assert obj.password.hash.decode('utf8').startswith('$pbkdf2-sha512$')
        assert obj.password == 'b'
