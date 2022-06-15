import pytest
import sqlalchemy as sa

from sqlalchemy_utils import EmailType


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        email = sa.Column(EmailType)

        def __repr__(self):
            return 'Building(%r)' % self.id
    return User


@pytest.fixture
def init_models(User):
    pass


class TestCaseInsensitiveComparator:

    def test_supports_equals(self, session, User):
        query = (
            session.query(User)
            .filter(User.email == 'email@example.com')
        )

        assert 'user.email = lower(?)' in str(query)

    def test_supports_in_(self, session, User):
        query = (
            session.query(User)
            .filter(User.email.in_(['email@example.com', 'a']))
        )
        assert (
            'user.email IN (lower(?), lower(?))'
            in str(query)
        )

    def test_supports_notin_(self, session, User):
        query = (
            session.query(User)
            .filter(User.email.notin_(['email@example.com', 'a']))
        )
        assert (
            'user.email NOT IN ('
            in str(query)
        )

    def test_does_not_apply_lower_to_types_that_are_already_lowercased(
        self,
        User
    ):
        assert str(User.email == User.email) == (
            '"user".email = "user".email'
        )
