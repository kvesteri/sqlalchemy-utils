from pytest import mark
import sqlalchemy as sa
from sqlalchemy_utils.types import url

from tests import TestCase


@mark.skipif('url.furl is None')
class TestURLType(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            website = sa.Column(url.URLType)

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_color_parameter_processing(self):
        user = self.User(
            website=url.furl(u'www.example.com')
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert isinstance(user.website, url.furl)

    def test_scalar_attributes_get_coerced_to_objects(self):
        user = self.User(website=u'www.example.com')

        assert isinstance(user.website, url.furl)
