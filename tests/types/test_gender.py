import pytest
import sqlalchemy as sa

from sqlalchemy_utils import GenderType


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        gender = sa.Column(GenderType)

        def __repr__(self):
            return 'User(%r)' % self.id
    return User


class TestGenderType(object):
    def test_saves_gender_as_lowercased(self, session, User):
        user = User(gender=u'Male')

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.gender == u'male'

    def test_literal_param(self, session, User):
        clause = User.gender == 'Female'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == '"user".gender = lower(\'Female\')'

    def test_nonbinary_gender(self, session, User):
        user = User(gender=u'non-binary')

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.gender == u'non-binary'
