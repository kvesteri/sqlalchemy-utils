import uuid

import pytest
import sqlalchemy as sa

from sqlalchemy_utils import UUIDType


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


class TestUUIDType(object):

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
