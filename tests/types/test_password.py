import unittest.mock as mock

import pytest
import sqlalchemy as sa
import sqlalchemy.dialects.mysql
import sqlalchemy.dialects.oracle
import sqlalchemy.dialects.postgresql
import sqlalchemy.dialects.sqlite
from sqlalchemy import inspect

from sqlalchemy_utils import Password, PasswordType, types  # noqa
from sqlalchemy_utils.compat import _select_args


@pytest.fixture
def extra_kwargs():
    """PasswordType extra keyword arguments."""
    return {}


@pytest.fixture
def User(Base, extra_kwargs):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        password = sa.Column(PasswordType(
            schemes=[
                'pbkdf2_sha512',
                'pbkdf2_sha256',
                'md5_crypt',
                'hex_md5'
            ],
            deprecated=['md5_crypt', 'hex_md5'],
            **extra_kwargs
        ))

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


@pytest.fixture
def init_models(User):
    pass


def onload_callback(schemes, deprecated):
    """
    Get onload callback that takes the PasswordType arguments from the config.
    """
    def onload(**kwargs):
        kwargs['schemes'] = schemes
        kwargs['deprecated'] = deprecated
        return kwargs
    return onload


@pytest.mark.skipif('types.password.passlib is None')
class TestPasswordType:
    @pytest.mark.parametrize('dialect_module,impl', [
        (sqlalchemy.dialects.sqlite, sa.dialects.sqlite.BLOB),
        (sqlalchemy.dialects.postgresql, sa.dialects.postgresql.BYTEA),
        (sqlalchemy.dialects.oracle, sa.dialects.oracle.RAW),
        (sqlalchemy.dialects.mysql, sa.VARBINARY),
    ])
    def test_load_dialect_impl(self, dialect_module, impl):
        """
        Should produce the same impl type as Alembic would expect after
        inspecing a database
        """
        password_type = PasswordType()
        assert isinstance(
            password_type.load_dialect_impl(dialect_module.dialect()),
            impl
        )

    def test_encrypt(self, User):
        """Should encrypt the password on setting the attribute."""
        obj = User()
        obj.password = b'b'

        assert obj.password.hash != 'b'
        assert obj.password.hash.startswith(b'$pbkdf2-sha512$')

    def test_check(self, session, User):
        """
        Should be able to compare the plaintext against the
        encrypted form.
        """
        obj = User()
        obj.password = 'b'

        assert obj.password == 'b'
        assert obj.password != 'a'

        session.add(obj)
        session.commit()

        try:
            obj = session.get(User, obj.id)
        except AttributeError:
            # sqlalchemy 1.3
            obj = session.query(User).get(obj.id)

        assert obj.password == b'b'
        assert obj.password != 'a'

    def test_check_and_update(self, User):
        """
        Should be able to compare the plaintext against a deprecated
        encrypted form and have it auto-update to the preferred version.
        """

        from passlib.hash import md5_crypt

        obj = User()
        obj.password = Password(md5_crypt.hash('b'))

        assert obj.password.hash.decode('utf8').startswith('$1$')
        assert obj.password == 'b'
        assert obj.password.hash.decode('utf8').startswith('$pbkdf2-sha512$')

    def test_auto_column_length(self, User):
        """Should derive the correct column length from the specified schemes.
        """

        from passlib.hash import pbkdf2_sha512

        kind = inspect(User).c.password.type

        # name + rounds + salt + hash + ($ * 4) of largest hash
        expected_length = len(pbkdf2_sha512.name)
        expected_length += len(str(pbkdf2_sha512.max_rounds))
        expected_length += pbkdf2_sha512.max_salt_size
        expected_length += pbkdf2_sha512.encoded_checksum_size
        expected_length += 4

        assert kind.length == expected_length

    def test_without_schemes(self):
        assert PasswordType(schemes=[]).length == 1024

    def test_compare(self, User):
        from passlib.hash import md5_crypt

        obj = User()
        obj.password = Password(md5_crypt.hash('b'))

        other = User()
        other.password = Password(md5_crypt.hash('b'))

        # Not sure what to assert here; the test raised an error before.
        assert obj.password != other.password

    def test_set_none(self, session, User):

        obj = User()
        obj.password = None

        assert obj.password is None

        session.add(obj)
        session.commit()

        try:
            obj = session.get(User, obj.id)
        except AttributeError:
            # sqlalchemy 1.3
            obj = session.query(User).get(obj.id)

        assert obj.password is None

    def test_update_none(self, session, User):
        """
        Should be able to change a password from ``None`` to a valid
        password.
        """

        obj = User()
        obj.password = None

        session.add(obj)
        session.commit()

        try:
            obj = session.get(User, obj.id)
        except AttributeError:
            # sqlalchemy 1.3
            obj = session.query(User).get(obj.id)
        obj.password = 'b'

        session.commit()

    def test_compare_none(self, User):
        """
        Should be able to compare a password of ``None``.
        """

        obj = User()
        obj.password = None

        assert obj.password is None
        assert obj.password == None  # noqa

        obj.password = 'b'

        assert obj.password is not None
        assert obj.password != None  # noqa

    def test_check_and_update_persist(self, session, User):
        """
        When a password is compared, the hash should update if needed to
        change the algorithm; and, commit to the database.
        """

        from passlib.hash import md5_crypt

        obj = User()
        obj.password = Password(md5_crypt.hash('b'))

        session.add(obj)
        session.commit()

        assert obj.password.hash.decode('utf8').startswith('$1$')
        assert obj.password == 'b'

        session.commit()

        try:
            obj = session.get(User, obj.id)
        except AttributeError:
            # sqlalchemy 1.3
            obj = session.query(User).get(obj.id)

        assert obj.password.hash.decode('utf8').startswith('$pbkdf2-sha512$')
        assert obj.password == 'b'

    @pytest.mark.parametrize(
        'extra_kwargs',
        [
            dict(
                onload=onload_callback(
                    schemes=['pbkdf2_sha256'],
                    deprecated=[],
                )
            )
        ]
    )
    def test_lazy_configuration(self, User):
        """
        Field should be able to read the passlib attributes lazily from the
        config (e.g. Flask config).
        """
        schemes = User.password.type.context.schemes()
        assert tuple(schemes) == ('pbkdf2_sha256',)
        obj = User()
        obj.password = b'b'
        assert obj.password.hash.decode('utf8').startswith('$pbkdf2-sha256$')

    @pytest.mark.parametrize('max_length', [1, 103])
    def test_constant_length(self, max_length):
        """
        Test that constant max_length is applied.
        """
        typ = PasswordType(max_length=max_length)
        assert typ.length == max_length

    def test_context_is_lazy(self):
        """
        Make sure the init doesn't evaluate the lazy context.
        """
        onload = mock.Mock(return_value={})
        PasswordType(onload=onload)
        assert not onload.called

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.password))
        # the type should be cacheable and not throw exception
        session.execute(query)
