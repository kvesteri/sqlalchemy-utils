import pytest
import six
import sqlalchemy as sa

from sqlalchemy_utils import ScalarListType


class TestScalarIntegerList(object):

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            some_list = sa.Column(ScalarListType(int))

            def __repr__(self):
                return 'User(%r)' % self.id

        return User

    @pytest.fixture
    def init_models(self, User):
        pass

    def test_save_integer_list(self, session, User):
        user = User(
            some_list=[1, 2, 3, 4]
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.some_list == [1, 2, 3, 4]


class TestScalarUnicodeList(object):

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            some_list = sa.Column(ScalarListType(six.text_type))

            def __repr__(self):
                return 'User(%r)' % self.id

        return User

    @pytest.fixture
    def init_models(self, User):
        pass

    def test_throws_exception_if_using_separator_in_list_values(
        self,
        session,
        User
    ):
        user = User(
            some_list=[u',']
        )

        session.add(user)
        with pytest.raises(sa.exc.StatementError) as db_err:
            session.commit()
        assert (
            "List values can't contain string ',' (its being used as "
            "separator. If you wish for scalar list values to contain "
            "these strings, use a different separator string.)"
        ) in str(db_err.value)

    def test_save_unicode_list(self, session, User):
        user = User(
            some_list=[u'1', u'2', u'3', u'4']
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.some_list == [u'1', u'2', u'3', u'4']

    def test_save_and_retrieve_empty_list(self, session, User):
        user = User(
            some_list=[]
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert user.some_list == []

    def test_compilation(self, User, session):
        query = sa.select([User.some_list])
        # the type should be cacheable and not throw exception
        session.execute(query)
