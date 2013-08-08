import sqlalchemy as sa
from sqlalchemy_utils import EmailType
from tests import TestCase


class TestEmailType(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            email = sa.Column(EmailType)

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_saves_email_as_lowercased(self):
        user = self.User(
            email=u'Someone@example.com'
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.email == u'someone@example.com'
