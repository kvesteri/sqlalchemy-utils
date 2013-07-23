import six
import sqlalchemy as sa
from sqlalchemy_utils import IPAddressType
from tests import TestCase


class TestIPAddressType(TestCase):
    def create_models(self):
        class Visitor(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            ip_address = sa.Column(IPAddressType)

            def __repr__(self):
                return 'Visitor(%r)' % self.id

        self.Visitor = Visitor

    def test_parameter_processing(self):
        visitor = self.Visitor(
            ip_address=u'111.111.111.111'
        )

        self.session.add(visitor)
        self.session.commit()

        visitor = self.session.query(self.Visitor).first()
        assert six.text_type(visitor.ip_address) == u'111.111.111.111'
