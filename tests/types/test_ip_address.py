import pytest
import sqlalchemy as sa

from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.types import ip_address


@pytest.fixture
def Visitor(Base):
    class Visitor(Base):
        __tablename__ = 'document'
        id = sa.Column(sa.Integer, primary_key=True)
        ip_address = sa.Column(ip_address.IPAddressType)

        def __repr__(self):
            return 'Visitor(%r)' % self.id
    return Visitor


@pytest.fixture
def init_models(Visitor):
    pass


@pytest.mark.skipif('ip_address.ip_address is None')
class TestIPAddressType:
    def test_parameter_processing(self, session, Visitor):
        visitor = Visitor(
            ip_address='111.111.111.111'
        )

        session.add(visitor)
        session.commit()

        visitor = session.query(Visitor).first()
        assert str(visitor.ip_address) == '111.111.111.111'

    def test_compilation(self, Visitor, session):
        query = sa.select(*_select_args(Visitor.ip_address))
        # the type should be cacheable and not throw exception
        session.execute(query)
