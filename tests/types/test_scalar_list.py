import six
import sqlalchemy as sa
from sqlalchemy_utils import ScalarListType
from pytest import raises
from tests import TestCase


class TestScalarIntegerList(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            some_list = sa.Column(ScalarListType(int))

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_save_integer_list(self):
        user = self.User(
            some_list=[1, 2, 3, 4]
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.some_list == [1, 2, 3, 4]


class TestScalarUnicodeList(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            some_list = sa.Column(ScalarListType(six.text_type))

            def __repr__(self):
                return 'User(%r)' % self.id

        self.User = User

    def test_throws_exception_if_using_separator_in_list_values(self):
        user = self.User(
            some_list=[u',']
        )

        self.session.add(user)
        with raises(sa.exc.StatementError) as db_err:
            self.session.commit()
        assert (
            "List values can't contain string ',' (its being used as "
            "separator. If you wish for scalar list values to contain "
            "these strings, use a different separator string.)"
        ) in str(db_err.value)

    def test_save_unicode_list(self):
        user = self.User(
            some_list=[u'1', u'2', u'3', u'4']
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.some_list == [u'1', u'2', u'3', u'4']

    def test_save_and_retrieve_empty_list(self):
        user = self.User(
            some_list=[]
        )

        self.session.add(user)
        self.session.commit()

        user = self.session.query(self.User).first()
        assert user.some_list == []
