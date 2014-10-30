"""
The functions in this module can be used for testing that the constraints of
your models. Each assert function runs SQL UPDATEs that check for the existence
of given constraint. Consider the following model::


    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(200), nullable=True)
        email = sa.Column(sa.String(255), nullable=False)


    user = User(name='John Doe', email='john@example.com')
    session.add(user)
    session.commit()


We can easily test the constraints by assert_* functions::


    from sqlalchemy_utils import (
        assert_nullable,
        assert_non_nullable,
        assert_max_length
    )

    assert_nullable(user, 'name')
    assert_non_nullable(user, 'email')
    assert_max_length(user, 'name', 200)

    # raises AssertionError because the max length of email is 255
    assert_max_length(user, 'email', 300)
"""
import sqlalchemy as sa
from sqlalchemy.exc import DataError, IntegrityError


class raises(object):
    def __init__(self, expected_exc):
        self.expected_exc = expected_exc

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type != self.expected_exc:
            return False
        return True


def _update_field(obj, field, value):
    session = sa.orm.object_session(obj)
    table = sa.inspect(obj.__class__).columns[field].table
    query = table.update().values(**{field: value})
    session.execute(query)
    session.flush()


def _expect_successful_update(obj, field, value, reraise_exc):
    try:
        _update_field(obj, field, value)
    except (reraise_exc) as e:
        session = sa.orm.object_session(obj)
        session.rollback()
        assert False, str(e)


def _expect_failing_update(obj, field, value, expected_exc):
    with raises(expected_exc):
        _update_field(obj, field, value)
    session = sa.orm.object_session(obj)
    session.rollback()


def assert_nullable(obj, column):
    """
    Assert that given column is nullable. This is checked by running an SQL
    update that assigns given column as None.

    :param obj: SQLAlchemy declarative model object
    :param column: Name of the column
    """
    _expect_successful_update(obj, column, None, IntegrityError)


def assert_non_nullable(obj, column):
    """
    Assert that given column is not nullable. This is checked by running an SQL
    update that assigns given column as None.

    :param obj: SQLAlchemy declarative model object
    :param column: Name of the column
    """
    _expect_failing_update(obj, column, None, IntegrityError)


def assert_max_length(obj, column, max_length):
    """
    Assert that the given column is of given max length.

    :param obj: SQLAlchemy declarative model object
    :param column: Name of the column
    """
    _expect_successful_update(obj, column, u'a' * max_length, DataError)
    _expect_failing_update(obj, column, u'a' * (max_length + 1), DataError)
