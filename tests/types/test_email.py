import pytest
import sqlalchemy as sa

from sqlalchemy_utils import EmailType
from sqlalchemy_utils.compat import _select_args


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        email = sa.Column(EmailType)
        short_email = sa.Column(EmailType(length=70))

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


class TestEmailType:
    def test_saves_email_as_lowercased(self, session, User):
        user = User(email='Someone@example.com')

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.email == 'someone@example.com'

    def test_literal_param(self, session, User):
        clause = User.email == 'Someone@example.com'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == '"user".email = lower(\'Someone@example.com\')'

    def test_custom_length(self, session, User):
        assert User.short_email.type.impl.length == 70

    def test_compilation(self, User, session):
        query = sa.select(*_select_args(User.email))
        # the type should be cacheable and not throw exception
        session.execute(query)
