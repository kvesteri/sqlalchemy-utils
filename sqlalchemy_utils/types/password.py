import six
import weakref
from sqlalchemy_utils import ImproperlyConfigured
from sqlalchemy import types

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


class PasswordType(types.TypeDecorator):
    """
    Hashes passwords as they come into the database and allows verifying
    them using a pythonic interface ::

        >>> target = Model()
        >>> target.password = 'b'
        '$5$rounds=80000$H.............'

        >>> target.password == 'b'
        True

    """

    impl = types.BINARY(60)

    python_type = Password

    def __init__(self, **kwargs):
        """
        All keyword arguments are forwarded to the construction of a
        `passlib.context.CryptContext` object.

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
                "'passlib' is required to use 'PasswordType'")

        # Construct the passlib crypt context.
        self.context = CryptContext(**kwargs)

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

    def coercion_listener(self, target, value, oldvalue, initiator):
        if not isinstance(value, Password):
            # Hash the password using the default scheme.
            value = self.context.encrypt(value).encode('utf8')
            return Password(value, context=self.context)

        else:
            # If were given a password object; ensure the context is right.
            value.context = weakref.proxy(self.context)

        return value
