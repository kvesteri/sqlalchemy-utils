from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import mssql, mysql, postgresql, sqlite

from sqlalchemy_utils.types.enriched_datetime import (
    enriched_datetime_type,
    pendulum_datetime
)


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'users'
        id = sa.Column(sa.Integer, primary_key=True)
        created_at = sa.Column(
            enriched_datetime_type.EnrichedDateTimeType(
                datetime_processor=pendulum_datetime.PendulumDateTime,
            ))
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('pendulum_datetime.pendulum is None')
class TestPendulumDateTimeType:

    def test_parameter_processing(self, session, User):
        user = User(
            created_at=pendulum_datetime.pendulum.datetime(1995, 7, 11)
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert isinstance(user.created_at, datetime)

        def test_int_coercion(self, User):
            user = User(
                created_at=1367900664
            )
            assert user.created_at.year == 2013

        def test_float_coercion(self, User):
            user = User(
                created_at=1367900664.0
            )
            assert user.created_at.year == 2013

    def test_string_coercion(self, User):
        user = User(
            created_at='1367900664'
        )
        assert user.created_at.year == 2013

    def test_utc(self, session, User):
        time = pendulum_datetime.pendulum.now("UTC")
        user = User(created_at=time)
        session.add(user)
        assert user.created_at == time
        session.commit()
        assert user.created_at == time

    @pytest.mark.usefixtures('postgresql_dsn')
    def test_utc_postgres(self, session, User):
        time = pendulum_datetime.pendulum.now("UTC")
        user = User(created_at=time)
        session.add(user)
        assert user.created_at == time
        session.commit()
        assert user.created_at == time

    def test_other_tz(self, session, User):
        time = pendulum_datetime.pendulum.now("UTC")
        local = time.in_tz('Asia/Tokyo')
        user = User(created_at=local)
        session.add(user)
        assert user.created_at == time == local
        session.commit()
        assert user.created_at == time

    def test_literal_param(self, session, User):
        clause = User.created_at > datetime(2015, 1, 1)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert compiled == "users.created_at > '2015-01-01 00:00:00'"

    @pytest.mark.parametrize('dialect', [sqlite, postgresql, mysql, mssql])
    @pytest.mark.parametrize('with_timezone', [False, True])
    @pytest.mark.parametrize('value_kind', ['pendulum', 'datetime', 'string'])
    def test_literal_binds(self, dialect, with_timezone, value_kind):
        value = datetime(2015, 1, 1, 15, 30, 45, tzinfo=timezone(timedelta(hours=2)))
        if value_kind == 'pendulum':
            value = pendulum_datetime.pendulum.instance(value)
        elif value_kind == 'string':
            value = value.isoformat()

        datetime_type = enriched_datetime_type.EnrichedDateTimeType(
            datetime_processor=pendulum_datetime.PendulumDateTime,
            timezone=with_timezone,
        )
        dialect = dialect.dialect()
        bound_value = datetime_type.process_bind_param(value, dialect)
        assert bound_value == datetime(2015, 1, 1, 13, 30, 45)
        assert bound_value.tzinfo is None

        column = sa.column('created_at', datetime_type)
        native_column = sa.column('created_at', sa.DateTime(timezone=with_timezone))
        compile_kwargs = {
            'dialect': dialect,
            'compile_kwargs': {'literal_binds': True},
        }
        assert str((column > value).compile(**compile_kwargs)) == str(
            (native_column > bound_value).compile(**compile_kwargs)
        )
