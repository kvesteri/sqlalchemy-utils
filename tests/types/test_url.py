import pytest
import sqlalchemy as sa

from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.types import url


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        website = sa.Column(url.URLType)

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('url.furl is None')
class TestURLType:
    def test_color_parameter_processing(self, session, User):
        user = User(
            website=url.furl('www.example.com')
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert isinstance(user.website, url.furl)

    def test_scalar_attributes_get_coerced_to_objects(self, User):
        user = User(website='www.example.com')

        assert isinstance(user.website, url.furl)

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.website))
        # the type should be cacheable and not throw exception
        session.execute(query)
