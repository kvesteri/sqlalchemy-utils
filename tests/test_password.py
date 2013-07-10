from pytest import mark
import sqlalchemy as sa
from tests import TestCase
from sqlalchemy_utils.types import password
from sqlalchemy_utils import Password, PasswordType, coercion_listener


@mark.xfail('password.passlib is None')
class TestPasswordType(TestCase):

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            password = sa.Column(PasswordType(
                schemes=[
                    'pbkdf2_sha512',
                    'md5_crypt'
                ],

                deprecated=['md5_crypt']
            ))

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User
        sa.event.listen(sa.orm.mapper, 'mapper_configured', coercion_listener)

    def test_encrypt(self):
        """Should encrypt the password on setting the attribute."""
        obj = self.User()
        obj.password = b'b'

        assert obj.password.raw != 'b'
        assert obj.password.raw.startswith(b'$pbkdf2-sha512$')

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

        assert obj.password.raw.startswith('$1$')
        assert obj.password == 'b'
        assert obj.password.raw.startswith('$pbkdf2-sha512$')
