import sqlalchemy as sa
from tests import TestCase
from sqlalchemy_utils import UUIDType
import uuid


class TestUUIDType(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(UUIDType, default=uuid.uuid4, primary_key=True)

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_commit(self):
        obj = self.User()
        obj.id = uuid.uuid4().hex

        self.session.add(obj)
        self.session.commit()

        u = self.session.query(self.User).one()

        assert u.id == obj.id

    def test_coerce(self):
        obj = self.User()
        obj.id = identifier = uuid.uuid4().hex

        assert isinstance(obj.id, uuid.UUID)
        assert obj.id.hex == identifier

        obj.id = identifier = uuid.uuid4().bytes

        assert isinstance(obj.id, uuid.UUID)
        assert obj.id.bytes == identifier
