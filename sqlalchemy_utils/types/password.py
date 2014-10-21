import six
import weakref
from sqlalchemy_utils.exceptions import ImproperlyConfigured
from sqlalchemy import types
from sqlalchemy.dialects import postgresql, oracle
from .scalar_coercible import ScalarCoercible
from sqlalchemy.ext.mutable import Mutable

passlib = None
try:
    import passlib
    from passlib.context import CryptContext
except ImportError:
    pass


class Password(Mutable, object):

    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, Password):
            return value

        if isinstance(value, (six.string_types, six.binary_type)):
            return cls(value, secret=True)

        super(Password, cls).coerce(key, value)

    def __init__(self, value, context=None, secret=False):
        # Store the hash (if it is one).
        self.hash = value if not secret else None

        # Store the secret if we have one.
        self.secret = value if secret else None

        # The hash should be bytes.
        if isinstance(self.hash, six.text_type):
            self.hash = self.hash.encode('utf8')

        # Save weakref of the password context (if we have one)
        self.context = weakref.proxy(context) if context is not None else None

    def __eq__(self, value):
        if self.hash is None or value is None:
            # Ensure that we don't continue comparison if one of us is None.
            return self.hash is value

        if isinstance(value, Password):
            # Comparing 2 hashes isn't very useful; but this equality
            # method breaks otherwise.
            return value.hash == self.hash

        if self.context is None:
            # Compare 2 hashes again as we don't know how to validate.
            return value == self

        if isinstance(value, (six.string_types, six.binary_type)):
            valid, new = self.context.verify_and_update(value, self.hash)
            if valid and new:
                # New hash was calculated due to various reasons; stored one
                # wasn't optimal, etc.
                self.hash = new

                # The hash should be bytes.
                if isinstance(self.hash, six.string_types):
                    self.hash = self.hash.encode('utf8')
                    self.changed()

            return valid

        return False

    def __ne__(self, value):
        return not (self == value)


class PasswordType(types.TypeDecorator, ScalarCoercible):
    """
    PasswordType hashes passwords as they come into the database and allows
    verifying them using a pythonic interface.

    All keyword arguments (aside from max_length) are forwarded to the
    construction of a `passlib.context.CryptContext` object.

    The following usage will create a password column that will
    automatically hash new passwords as `pbkdf2_sha512` but still compare
    passwords against pre-existing `md5_crypt` hashes. As passwords are
    compared; the password hash in the database will be updated to
    be `pbkdf2_sha512`.

    ::


        class Model(Base):
            password = sa.Column(PasswordType(
                schemes=[
                    'pbkdf2_sha512',
                    'md5_crypt'
                ],

                deprecated=['md5_crypt']
            ))


    Verifying password is as easy as:

    ::

        target = Model()
        target.password = 'b'
        # '$5$rounds=80000$H.............'

        target.password == 'b'
        # True

    """

    impl = types.VARBINARY(1024)
    python_type = Password

    def __init__(self, max_length=None, **kwargs):
        # Fail if passlib is not found.
        if passlib is None:
            raise ImproperlyConfigured(
                "'passlib' is required to use 'PasswordType'"
            )

        # Construct the passlib crypt context.
        self.context = CryptContext(**kwargs)

        if max_length is None:
            max_length = self.calculate_max_length()

        # Set the length to the now-calculated max length.
        self.length = max_length

    def calculate_max_length(self):
        # Calculate the largest possible encoded password.
        # name + rounds + salt + hash + ($ * 4) of largest hash
        max_lengths = [1024]
        for name in self.context.schemes():
            scheme = getattr(__import__('passlib.hash').hash, name)
            length = 4 + len(scheme.name)
            length += len(str(getattr(scheme, 'max_rounds', '')))
            length += (getattr(scheme, 'max_salt_size', 0) or 0)
            length += getattr(
                scheme,
                'encoded_checksum_size',
                scheme.checksum_size
            )
            max_lengths.append(length)

        # Return the maximum calculated max length.
        return max(max_lengths)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use a BYTEA type for postgresql.
            impl = postgresql.BYTEA(self.length)
            return dialect.type_descriptor(impl)
        if dialect.name == 'oracle':
            # Use a RAW type for oracle.
            impl = oracle.RAW(self.length)
            return dialect.type_descriptor(impl)

        # Use a VARBINARY for all other dialects.
        impl = types.VARBINARY(self.length)
        return dialect.type_descriptor(impl)

    def process_bind_param(self, value, dialect):
        if isinstance(value, Password):
            # If were given a password secret; encrypt it.
            if value.secret is not None:
                return self.context.encrypt(value.secret).encode('utf8')

            # Value has already been hashed.
            return value.hash

        if isinstance(value, six.string_types):
            # Assume value has not been hashed.
            return self.context.encrypt(value).encode('utf8')

    def process_result_value(self, value, dialect):
        if value is not None:
            return Password(value, self.context)

    def _coerce(self, value):

        if value is None:
            return

        if not isinstance(value, Password):
            # Hash the password using the default scheme.
            value = self.context.encrypt(value).encode('utf8')
            return Password(value, context=self.context)

        else:
            # If were given a password object; ensure the context is right.
            value.context = weakref.proxy(self.context)

            # If were given a password secret; encrypt it.
            if value.secret is not None:
                value.hash = self.context.encrypt(value.secret).encode('utf8')
                value.secret = None

        return value


Password.associate_with(PasswordType)
