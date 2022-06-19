import pytest
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy_utils import (
    assert_max_length,
    assert_max_value,
    assert_min_value,
    assert_non_nullable,
    assert_nullable
)


@pytest.fixture()
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column('_id', sa.Integer, primary_key=True)
        name = sa.Column('_name', sa.String(20))
        age = sa.Column('_age', sa.Integer, nullable=False)
        email = sa.Column(
            '_email', sa.String(200), nullable=False, unique=True
        )
        fav_numbers = sa.Column('_fav_numbers', ARRAY(sa.Integer))

        __table_args__ = (
            sa.CheckConstraint(sa.and_(age >= 0, age <= 150)),
            sa.CheckConstraint(
                sa.and_(
                    sa.func.array_length(fav_numbers, 1) <= 8
                )
            )
        )
    return User


@pytest.fixture()
def user(User, session):
    user = User(
        name='Someone',
        email='someone@example.com',
        age=15,
        fav_numbers=[1, 2, 3]
    )
    session.add(user)
    session.commit()
    return user


@pytest.mark.usefixtures('postgresql_dsn')
class TestAssertMaxLengthWithArray:

    def test_with_max_length(self, user):
        assert_max_length(user, 'fav_numbers', 8)
        assert_max_length(user, 'fav_numbers', 8)

    def test_smaller_than_max_length(self, user):
        with pytest.raises(AssertionError):
            assert_max_length(user, 'fav_numbers', 7)
        with pytest.raises(AssertionError):
            assert_max_length(user, 'fav_numbers', 7)

    def test_bigger_than_max_length(self, user):
        with pytest.raises(AssertionError):
            assert_max_length(user, 'fav_numbers', 9)
        with pytest.raises(AssertionError):
            assert_max_length(user, 'fav_numbers', 9)


@pytest.mark.usefixtures('postgresql_dsn')
class TestAssertNonNullable:

    def test_non_nullable_column(self, user):
        # Test everything twice so that session gets rolled back properly
        assert_non_nullable(user, 'age')
        assert_non_nullable(user, 'age')

    def test_nullable_column(self, user):
        with pytest.raises(AssertionError):
            assert_non_nullable(user, 'name')
        with pytest.raises(AssertionError):
            assert_non_nullable(user, 'name')


@pytest.mark.usefixtures('postgresql_dsn')
class TestAssertNullable:

    def test_nullable_column(self, user):
        assert_nullable(user, 'name')
        assert_nullable(user, 'name')

    def test_non_nullable_column(self, user):
        with pytest.raises(AssertionError):
            assert_nullable(user, 'age')
        with pytest.raises(AssertionError):
            assert_nullable(user, 'age')


@pytest.mark.usefixtures('postgresql_dsn')
class TestAssertMaxLength:

    def test_with_max_length(self, user):
        assert_max_length(user, 'name', 20)
        assert_max_length(user, 'name', 20)

    def test_with_non_nullable_column(self, user):
        assert_max_length(user, 'email', 200)
        assert_max_length(user, 'email', 200)

    def test_smaller_than_max_length(self, user):
        with pytest.raises(AssertionError):
            assert_max_length(user, 'name', 19)
        with pytest.raises(AssertionError):
            assert_max_length(user, 'name', 19)

    def test_bigger_than_max_length(self, user):
        with pytest.raises(AssertionError):
            assert_max_length(user, 'name', 21)
        with pytest.raises(AssertionError):
            assert_max_length(user, 'name', 21)


@pytest.mark.usefixtures('postgresql_dsn')
class TestAssertMinValue:

    def test_with_min_value(self, user):
        assert_min_value(user, 'age', 0)
        assert_min_value(user, 'age', 0)

    def test_smaller_than_min_value(self, user):
        with pytest.raises(AssertionError):
            assert_min_value(user, 'age', -1)
        with pytest.raises(AssertionError):
            assert_min_value(user, 'age', -1)

    def test_bigger_than_min_value(self, user):
        with pytest.raises(AssertionError):
            assert_min_value(user, 'age', 1)
        with pytest.raises(AssertionError):
            assert_min_value(user, 'age', 1)


@pytest.mark.usefixtures('postgresql_dsn')
class TestAssertMaxValue:

    def test_with_min_value(self, user):
        assert_max_value(user, 'age', 150)
        assert_max_value(user, 'age', 150)

    def test_smaller_than_max_value(self, user):
        with pytest.raises(AssertionError):
            assert_max_value(user, 'age', 149)
        with pytest.raises(AssertionError):
            assert_max_value(user, 'age', 149)

    def test_bigger_than_max_value(self, user):
        with pytest.raises(AssertionError):
            assert_max_value(user, 'age', 151)
        with pytest.raises(AssertionError):
            assert_max_value(user, 'age', 151)
