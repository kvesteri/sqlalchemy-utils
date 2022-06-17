import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from sqlalchemy_utils import UUIDType
from sqlalchemy_utils.compat import _select_args


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(UUIDType, default=uuid.uuid4, primary_key=True)

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


@pytest.fixture
def init_models(User):
    pass


class TestUUIDType:
    def test_repr(self):
        plain = UUIDType()
        assert repr(plain) == 'UUIDType()'

        text = UUIDType(binary=False)
        assert repr(text) == 'UUIDType(binary=False)'

        not_native = UUIDType(native=False)
        assert repr(not_native) == 'UUIDType(native=False)'

    def test_commit(self, session, User):
        obj = User()
        obj.id = uuid.uuid4().hex

        session.add(obj)
        session.commit()

        u = session.query(User).one()

        assert u.id == obj.id

    def test_coerce(self, User):
        obj = User()
        obj.id = identifier = uuid.uuid4().hex

        assert isinstance(obj.id, uuid.UUID)
        assert obj.id.hex == identifier

        obj.id = identifier = uuid.uuid4().bytes

        assert isinstance(obj.id, uuid.UUID)
        assert obj.id.bytes == identifier

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.id))

        # the type should be cacheable and not throw exception
        session.execute(query)

    def test_literal_bind(self, User):
        expr = (User.id == 'b4e794d6-5750-4844-958c-fa382649719d').compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True}
        )
        assert str(expr) == (
            '''"user".id = \'b4e794d6-5750-4844-958c-fa382649719d\''''
        )
