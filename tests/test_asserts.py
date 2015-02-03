import sqlalchemy as sa
import pytest
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy_utils import (
    assert_min_value,
    assert_max_length,
    assert_max_value,
    assert_nullable,
    assert_non_nullable
)
from sqlalchemy_utils.asserts import raises

from tests import TestCase


class TestRaises(object):
    def test_matching_exception(self):
        with raises(Exception):
            raise Exception()
        assert True

    def test_non_matchin_exception(self):
        with pytest.raises(Exception):
            with raises(ValueError):
                raise Exception()


class AssertionTestCase(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(20))
            age = sa.Column(sa.Integer, nullable=False)
            email = sa.Column(sa.String(200), nullable=False, unique=True)
            fav_numbers = sa.Column(ARRAY(sa.Integer))

            __table_args__ = (
                sa.CheckConstraint(sa.and_(age >= 0, age <= 150)),
                sa.CheckConstraint(
                    sa.and_(
                        sa.func.array_length(fav_numbers, 1) <= 8
                    )
                )
            )

        self.User = User

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        user = self.User(
            name='Someone',
            email='someone@example.com',
            age=15,
            fav_numbers=[1, 2, 3]
        )
        self.session.add(user)
        self.session.commit()
        self.user = user


class TestAssertMaxLengthWithArray(AssertionTestCase):
    def test_with_max_length(self):
        assert_max_length(self.user, 'fav_numbers', 8)
        assert_max_length(self.user, 'fav_numbers', 8)

    def test_smaller_than_max_length(self):
        with raises(AssertionError):
            assert_max_length(self.user, 'fav_numbers', 7)
        with raises(AssertionError):
            assert_max_length(self.user, 'fav_numbers', 7)

    def test_bigger_than_max_length(self):
        with raises(AssertionError):
            assert_max_length(self.user, 'fav_numbers', 9)
        with raises(AssertionError):
            assert_max_length(self.user, 'fav_numbers', 9)


class TestAssertNonNullable(AssertionTestCase):
    def test_non_nullable_column(self):
        # Test everything twice so that session gets rolled back properly
        assert_non_nullable(self.user, 'age')
        assert_non_nullable(self.user, 'age')

    def test_nullable_column(self):
        with raises(AssertionError):
            assert_non_nullable(self.user, 'name')
        with raises(AssertionError):
            assert_non_nullable(self.user, 'name')


class TestAssertNullable(AssertionTestCase):
    def test_nullable_column(self):
        assert_nullable(self.user, 'name')
        assert_nullable(self.user, 'name')

    def test_non_nullable_column(self):
        with raises(AssertionError):
            assert_nullable(self.user, 'age')
        with raises(AssertionError):
            assert_nullable(self.user, 'age')


class TestAssertMaxLength(AssertionTestCase):
    def test_with_max_length(self):
        assert_max_length(self.user, 'name', 20)
        assert_max_length(self.user, 'name', 20)

    def test_with_non_nullable_column(self):
        assert_max_length(self.user, 'email', 200)
        assert_max_length(self.user, 'email', 200)

    def test_smaller_than_max_length(self):
        with raises(AssertionError):
            assert_max_length(self.user, 'name', 19)
        with raises(AssertionError):
            assert_max_length(self.user, 'name', 19)

    def test_bigger_than_max_length(self):
        with raises(AssertionError):
            assert_max_length(self.user, 'name', 21)
        with raises(AssertionError):
            assert_max_length(self.user, 'name', 21)


class TestAssertMinValue(AssertionTestCase):
    def test_with_min_value(self):
        assert_min_value(self.user, 'age', 0)
        assert_min_value(self.user, 'age', 0)

    def test_smaller_than_min_value(self):
        with raises(AssertionError):
            assert_min_value(self.user, 'age', -1)
        with raises(AssertionError):
            assert_min_value(self.user, 'age', -1)

    def test_bigger_than_min_value(self):
        with raises(AssertionError):
            assert_min_value(self.user, 'age', 1)
        with raises(AssertionError):
            assert_min_value(self.user, 'age', 1)


class TestAssertMaxValue(AssertionTestCase):
    def test_with_min_value(self):
        assert_max_value(self.user, 'age', 150)
        assert_max_value(self.user, 'age', 150)

    def test_smaller_than_max_value(self):
        with raises(AssertionError):
            assert_max_value(self.user, 'age', 149)
        with raises(AssertionError):
            assert_max_value(self.user, 'age', 149)

    def test_bigger_than_max_value(self):
        with raises(AssertionError):
            assert_max_value(self.user, 'age', 151)
        with raises(AssertionError):
            assert_max_value(self.user, 'age', 151)
