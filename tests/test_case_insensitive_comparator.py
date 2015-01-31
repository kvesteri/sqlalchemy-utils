import sqlalchemy as sa
from sqlalchemy_utils import EmailType
from tests import TestCase


class TestCaseInsensitiveComparator(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            email = sa.Column(EmailType)

            def __repr__(self):
                return 'Building(%r)' % self.id

        self.User = User

    def test_supports_equals(self):
        query = (
            self.session.query(self.User)
            .filter(self.User.email == u'email@example.com')
        )

        assert '"user".email = lower(:lower_1)' in str(query)

    def test_supports_in_(self):
        query = (
            self.session.query(self.User)
            .filter(self.User.email.in_([u'email@example.com', u'a']))
        )
        assert (
            '"user".email IN (lower(:lower_1), lower(:lower_2))'
            in str(query)
        )

    def test_supports_notin_(self):
        query = (
            self.session.query(self.User)
            .filter(self.User.email.notin_([u'email@example.com', u'a']))
        )
        assert (
            '"user".email NOT IN (lower(:lower_1), lower(:lower_2))'
            in str(query)
        )

    def test_does_not_apply_lower_to_types_that_are_already_lowercased(self):
        assert str(self.User.email == self.User.email) == (
            '"user".email = "user".email'
        )
