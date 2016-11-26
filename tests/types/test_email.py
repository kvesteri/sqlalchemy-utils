import pytest
import sqlalchemy as sa

from sqlalchemy_utils import EmailType


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        email = sa.Column(EmailType)
        short_email = sa.Column(EmailType(length=70))
        non_lowercase_email = sa.Column(EmailType(lowercase=False))

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


class TestEmailType(object):
    def test_saves_email_as_lowercased(self, session, User):
        user = User(email=u'Someone@example.com')

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.email == u'someone@example.com'

    def test_non_lowercase(self, session, User):
        """If the column is configured to not convert emails to lowercase,
        it does so.
        """
        expected_email = u'Someone@example.com'
        user = User(non_lowercase_email=expected_email)

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.non_lowercase_email == expected_email

    def test_literal_param(self, session, User):
        clause = User.email == 'Someone@example.com'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == '"user".email = lower(\'Someone@example.com\')'

    def test_custom_length(self, session, User):
        assert User.short_email.type.impl.length == 70
