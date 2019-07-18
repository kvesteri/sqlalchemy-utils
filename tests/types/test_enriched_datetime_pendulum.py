from __future__ import unicode_literals

from datetime import date, datetime

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.types import enriched_datetime


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'users'
        id = sa.Column(sa.Integer, primary_key=True)
        birthday = sa.Column(
            enriched_datetime.EnrichedDateType(type="pendulum"))
        created_at = sa.Column(
            enriched_datetime.EnrichedDateTimeType(type="pendulum"))
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('enriched_datetime.pendulum is None')
class TestPendulumDateType(object):

    def test_parameter_processing(self, session, User):
        user = User(
            birthday=enriched_datetime.pendulum.date(1995, 7, 11)
        )

        session.add(user)
        session.commit()

        user = session.query(User).first()
        assert isinstance(user.birthday, date)

    def test_int_coercion(self, User):
        user = User(
            birthday=1367900664
        )
        assert user.birthday.year == 2013

    def test_string_coercion(self, User):
        user = User(
            birthday='1367900664'
        )
        assert user.birthday.year == 2013

    def test_utc(self, session, User):
        time = enriched_datetime.pendulum.now("UTC")
        user = User(birthday=time)
        session.add(user)
        assert user.birthday == time
        session.commit()
        assert user.birthday == time.date()

    def test_literal_param(self, session, User):
        clause = User.birthday > '2015-01-01'
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert compiled == 'users.birthday > 2015-01-01'


@pytest.mark.skipif('enriched_datetime.pendulum is None')
class TestPendulumDateTimeType(object):

    def test_parameter_processing(self, session, User):
        user = User(
            created_at=enriched_datetime.pendulum.datetime(1995, 7, 11)
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
        time = enriched_datetime.pendulum.now("UTC")
        user = User(created_at=time)
        session.add(user)
        assert user.created_at == time
        session.commit()
        assert user.created_at == time

    def test_other_tz(self, session, User):
        time = enriched_datetime.pendulum.now("UTC")
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
