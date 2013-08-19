import six
import weakref
from sqlalchemy_utils import ImproperlyConfigured
from sqlalchemy import types
from sqlalchemy.dialects import postgresql
from .scalar_coercible import ScalarCoercible

try:
    import passlib
    from passlib.context import CryptContext

except ImportError:
    passlib = None


class Password(object):

    def __init__(self, value, context=None):
        # Store the hash.
        self.hash = value

        # Save weakref of the password context (if we have one)
        if context is not None:
            self.context = weakref.proxy(context)

    def __eq__(self, value):
        valid, new = self.context.verify_and_update(value, self.hash)
        if valid and new:
            # New hash was calculated due to various reasons; stored one
            # wasn't optimal, etc.
            self.hash = new
        return valid

    def __ne__(self, value):
        return not (self == value)


class PasswordType(types.TypeDecorator, ScalarCoercible):
    """
    Hashes passwords as they come into the database and allows verifying
    them using a pythonic interface ::

        >>> target = Model()
        >>> target.password = 'b'
        '$5$rounds=80000$H.............'

        >>> target.password == 'b'
        True

    """

    impl = types.VARBINARY(1024)

    python_type = Password

    def __init__(self, max_length=None, **kwargs):
        """
        All keyword arguments (aside from max_length) are
        forwarded to the construction of a `passlib.context.CryptContext`
        object.

        The following usage will create a password column that will
        automatically hash new passwords as `pbkdf2_sha512` but still compare
        passwords against pre-existing `md5_crypt` hashes. As passwords are
        compared; the password hash in the database will be updated to
        be `pbkdf2_sha512`. ::

            class Model(Base):
                password = sa.Column(PasswordType(
                    schemes=[
                        'pbkdf2_sha512',
                        'md5_crypt'
                    ],

                    deprecated=['md5_crypt']
                ))

        """

        # Bail if passlib is not found.
        if passlib is None:
            raise ImproperlyConfigured(
                "'passlib' is required to use 'PasswordType'"
            )

        # Construct the passlib crypt context.
        self.context = CryptContext(**kwargs)

        if max_length is None:
            # Calculate the largest possible encoded password.
            # name + rounds + salt + hash + ($ * 4) of largest hash
            max_lengths = [1024]
            for name in self.context.schemes():
                scheme = getattr(__import__('passlib.hash').hash, name)
                length = 4 + len(scheme.name)
                length += len(str(getattr(scheme, 'max_rounds', '')))
                length += scheme.max_salt_size or 0
                length += getattr(
                    scheme,
                    'encoded_checksum_size',
                    scheme.checksum_size
                )
                max_lengths.append(length)

            # Set the max_length to the maximum calculated max length.
            max_length = max(max_lengths)

        # Set the length to the now-calculated max length.
        self.length = max_length

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use a BYTEA type for postgresql.
            impl = postgresql.BYTEA(self.length)
            return dialect.type_descriptor(impl)

        # Use a VARBINARY for all other dialects.
        impl = types.VARBINARY(self.length)
        return dialect.type_descriptor(impl)

    def process_bind_param(self, value, dialect):
        if isinstance(value, Password):
            # Value has already been hashed.
            return value.hash

        if isinstance(value, six.string_types):
            # Assume value has not been hashed.
            return self.context.encrypt(value).encode('utf8')

    def process_result_value(self, value, dialect):
        if value is not None:
            return Password(value, self.context)

    def _coerce(self, value):
        if not isinstance(value, Password):
            # Hash the password using the default scheme.
            value = self.context.encrypt(value).encode('utf8')
            return Password(value, context=self.context)

        else:
            # If were given a password object; ensure the context is right.
            value.context = weakref.proxy(self.context)

        return value
