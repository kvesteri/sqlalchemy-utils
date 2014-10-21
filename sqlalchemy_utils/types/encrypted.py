# -*- coding: utf-8 -*-
import base64
import six
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy_utils.exceptions import ImproperlyConfigured

cryptography = None
try:
    import cryptography
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers import(
        Cipher, algorithms, modes
    )
    from cryptography.fernet import Fernet
except ImportError:
    pass


class EncryptionDecryptionBaseEngine(object):
    """A base encryption and decryption engine.

    This class must be sub-classed in order to create
    new engines.
    """

    def __init__(self, key):
        """Initialize a base engine."""
        if isinstance(key, six.string_types):
            key = six.b(key)
        self._digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        self._digest.update(key)
        self._engine_key = self._digest.finalize()

    def encrypt(self, value):
        raise NotImplementedError('Subclasses must implement this!')

    def decrypt(self, value):
        raise NotImplementedError('Subclasses must implement this!')


class AesEngine(EncryptionDecryptionBaseEngine):
    """Provide AES encryption and decryption methods."""

    BLOCK_SIZE = 16
    PADDING = six.b('*')

    def __init__(self, key):
        super(AesEngine, self).__init__(key)
        self._initialize_engine(self._engine_key)

    def _update_key(self, new_key):
        parent = EncryptionDecryptionBaseEngine(new_key)
        self._initialize_engine(parent._engine_key)

    def _initialize_engine(self, parent_class_key):
        self.secret_key = parent_class_key
        self.iv = self.secret_key[:16]
        self.cipher = Cipher(
            algorithms.AES(self.secret_key),
            modes.CBC(self.iv),
            backend=default_backend()
        )

    def _pad(self, value):
        """Pad the message to be encrypted, if needed."""
        BS = self.BLOCK_SIZE
        P = self.PADDING
        padded = (value + (BS - len(value) % BS) * P)
        return padded

    def encrypt(self, value):
        if not isinstance(value, six.string_types):
            value = repr(value)
        if isinstance(value, six.text_type):
            value = str(value)
        value = six.b(value)
        value = self._pad(value)
        encryptor = self.cipher.encryptor()
        encrypted = encryptor.update(value) + encryptor.finalize()
        encrypted = base64.b64encode(encrypted)
        return encrypted

    def decrypt(self, value):
        if isinstance(value, six.text_type):
            value = str(value)
        decryptor = self.cipher.decryptor()
        decrypted = base64.b64decode(value)
        decrypted = decryptor.update(decrypted)+decryptor.finalize()
        decrypted = decrypted.rstrip(self.PADDING)
        if not isinstance(decrypted, six.string_types):
            decrypted = decrypted.decode('utf-8')
        return decrypted


class FernetEngine(EncryptionDecryptionBaseEngine):
    """Provide Fernet encryption and decryption methods."""

    def __init__(self, key):
        super(FernetEngine, self).__init__(key)
        self._initialize_engine(self._engine_key)

    def _update_key(self, new_key):
        parent = EncryptionDecryptionBaseEngine(new_key)
        self._initialize_engine(parent._engine_key)

    def _initialize_engine(self, parent_class_key):
        self.secret_key = base64.urlsafe_b64encode(parent_class_key)
        self.fernet = Fernet(self.secret_key)

    def encrypt(self, value):
        if not isinstance(value, six.string_types):
            value = repr(value)
        if isinstance(value, six.text_type):
            value = str(value)
        value = six.b(value)
        encrypted = self.fernet.encrypt(value)
        return encrypted

    def decrypt(self, value):
        if isinstance(value, six.text_type):
            value = str(value)
        decrypted = self.fernet.decrypt(value)
        if not isinstance(decrypted, six.string_types):
            decrypted = decrypted.decode('utf-8')
        return decrypted


class EncryptedType(TypeDecorator):
    """
    EncryptedType provides a way to encrypt and decrypt values,
    to and from databases, that their type is a basic SQLAlchemy type.
    For example Unicode, String or even Boolean.
    On the way in, the value is encrypted and on the way out the stored value
    is decrypted.

    EncryptedType needs Cryptography_ library in order to work.
    A simple example is given below.

    .. _Cryptography: https://cryptography.io/en/latest/

    ::

        import sqlalchemy as sa
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy_utils import EncryptedType


        secret_key = 'secretkey1234'
        # setup
        engine = create_engine('sqlite:///:memory:')
        connection = engine.connect()
        Base = declarative_base()

        class User(Base):
            __tablename__ = "user"
            id = sa.Column(sa.Integer, primary_key=True)
            username = sa.Column(EncryptedType(sa.Unicode, secret_key))
            access_token = sa.Column(EncryptedType(sa.String, secret_key))
            is_active = sa.Column(EncryptedType(sa.Boolean, secret_key))
            number_of_accounts = sa.Column(EncryptedType(sa.Integer,
                                                         secret_key))

        sa.orm.configure_mappers()
        Base.metadata.create_all(connection)

        # create a configured "Session" class
        Session = sessionmaker(bind=connection)

        # create a Session
        session = Session()

        # example
        user_name = u'secret_user'
        test_token = 'atesttoken'
        active = True
        num_of_accounts = 2

        user = User(username=user_name, access_token=test_token,
                    is_active=active, accounts_num=accounts)
        session.add(user)
        session.commit()

        print('id: {}'.format(user.id))
        print('username: {}'.format(user.username))
        print('token: {}'.format(user.access_token))
        print('active: {}'.format(user.is_active))
        print('accounts: {}'.format(user.accounts_num))

        # teardown
        session.close_all()
        Base.metadata.drop_all(connection)
        connection.close()
        engine.dispose()
    """

    impl = String

    def __init__(self, type_in=None, key=None, engine=None, **kwargs):
        """Initialization."""
        if not cryptography:
            raise ImproperlyConfigured(
                "'cryptography' is required to use EncryptedType"
            )
        super(EncryptedType, self).__init__(**kwargs)
        # set the underlying type
        if type_in is None:
            type_in = String()
        self.underlying_type = type_in()
        self._key = key
        if not engine:
            engine = AesEngine
        self.engine = engine(self._key)

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value
        self.engine._update_key(self._key)

    def process_bind_param(self, value, dialect):
        """Encrypt a value on the way in."""
        return self.engine.encrypt(value)

    def process_result_value(self, value, dialect):
        """Decrypt value on the way out."""
        decrypted_value = self.engine.decrypt(value)
        return self.underlying_type.python_type(decrypted_value)
