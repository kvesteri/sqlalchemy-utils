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
            return 'User(%r)' % self.id
    return User


class TestEmailType(object):
    def test_saves_email_as_lowercased(self, session, User):
        user = User(email=u'Someone@example.com')

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.email == u'someone@example.com'

    def test_literal_param(self, session, User):
        clause = User.email == 'Someone@example.com'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == '"user".email = lower(\'Someone@example.com\')'
