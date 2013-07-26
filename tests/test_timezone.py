from pytest import mark
import six
import sqlalchemy as sa
from sqlalchemy_utils.types import timezone
from tests import TestCase


try:
    import dateutil

except ImportError:
    dateutil = None


@mark.skipif('dateutil is None')
class TestTimezoneType(TestCase):
    def create_models(self):
        class Visitor(self.Base):
            __tablename__ = 'document'
            id = sa.Column(sa.Integer, primary_key=True)
            timezone = sa.Column(timezone.TimezoneType)

            def __repr__(self):
                return 'Visitor(%r)' % self.id

        self.Visitor = Visitor

    def test_parameter_processing(self):
        visitor = self.Visitor(
            timezone=u'America/Los_Angeles'
        )

        self.session.add(visitor)
        self.session.commit()

        visitor = self.session.query(self.Visitor).filter_by(
            timezone='America/Los_Angeles').first()

        assert visitor is not None
