from __future__ import unicode_literals

from datetime import date, datetime

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.types.enriched_datetime import enriched_datetime_type


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'users'
        id = sa.Column(sa.Integer, primary_key=True)
        created_at = sa.Column(
            enriched_datetime_type.EnrichedDateTimeType(type="pendulum"))
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('enriched_datetime.pendulum is None')
class TestPendulumDateTimeType(object):

    def test_parameter_processing(self, session, User):
        user = User(
            created_at=enriched_datetime_type.pendulum.datetime(1995, 7, 11)
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

    def test_string_coercion(self, User):
        user = User(
            created_at='1367900664'
        )
        assert user.created_at.year == 2013

    def test_utc(self, session, User):
        time = enriched_datetime_type.pendulum.now("UTC")
        user = User(created_at=time)
        session.add(user)
        assert user.created_at == time
        session.commit()
        assert user.created_at == time

    def test_other_tz(self, session, User):
        time = enriched_datetime_type.pendulum.now("UTC")
        local = time.in_tz('Asia/Tokyo')
        user = User(created_at=local)
        session.add(user)
        assert user.created_at == time == local
        session.commit()
        assert user.created_at == time

    def test_literal_param(self, session, User):
        clause = User.created_at > '2015-01-01'
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert compiled == 'users.created_at > 2015-01-01'
