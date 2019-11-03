from __future__ import unicode_literals

from datetime import date, datetime

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.types.enriched_datetime import enriched_date_type


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'users'
        id = sa.Column(sa.Integer, primary_key=True)
        birthday = sa.Column(
            enriched_date_type.EnrichedDateType(type="pendulum"))
    return User


@pytest.fixture
def init_models(User):
    pass


@pytest.mark.skipif('enriched_date_type.pendulum is None')
class TestPendulumDateType(object):

    def test_parameter_processing(self, session, User):
        user = User(
            birthday=enriched_date_type.pendulum.date(1995, 7, 11)
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
        time = enriched_date_type.pendulum.now("UTC")
        user = User(birthday=time)
        session.add(user)
        assert user.birthday == time
        session.commit()
        assert user.birthday == time.date()

    def test_literal_param(self, session, User):
        clause = User.birthday > '2015-01-01'
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert compiled == 'users.birthday > 2015-01-01'
