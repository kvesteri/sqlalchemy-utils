from datetime import datetime

import pytest
import sqlalchemy as sa
from dateutil import tz

from sqlalchemy_utils.types import arrow


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        created_at = sa.Column(arrow.ArrowType)
        published_at = sa.Column(arrow.ArrowType(timezone=True))
        published_at_dt = sa.Column(sa.DateTime(timezone=True))
    return Article


@pytest.fixture
def init_models(Article):
    pass


@pytest.mark.skipif('arrow.arrow is None')
class TestArrowDateTimeType(object):
    def test_parameter_processing(self, session, Article):
        article = Article(
            created_at=arrow.arrow.get(datetime(2000, 11, 1))
        )

        session.add(article)
        session.commit()

        article = session.query(Article).first()
        assert article.created_at.datetime

    def test_string_coercion(self, Article):
        article = Article(
            created_at='2013-01-01'
        )
        assert article.created_at.year == 2013

    def test_utc(self, session, Article):
        time = arrow.arrow.utcnow()
        article = Article(created_at=time)
        session.add(article)
        assert article.created_at == time
        session.commit()
        assert article.created_at == time

    def test_other_tz(self, session, Article):
        time = arrow.arrow.utcnow()
        local = time.to('US/Pacific')
        article = Article(created_at=local)
        session.add(article)
        assert article.created_at == time == local
        session.commit()
        assert article.created_at == time

    def test_literal_param(self, session, Article):
        clause = Article.created_at > '2015-01-01'
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert compiled == "article.created_at > '2015-01-01'"

    @pytest.mark.usefixtures('postgresql_dsn')
    def test_timezone(self, session, Article):
        timezone = tz.gettz('Europe/Stockholm')
        dt = arrow.arrow.get(datetime(2015, 1, 1, 15, 30, 45), timezone)
        article = Article(published_at=dt, published_at_dt=dt.datetime)

        session.add(article)
        session.commit()
        session.expunge_all()

        item = session.query(Article).one()
        assert item.published_at.datetime == item.published_at_dt
        assert item.published_at.to(timezone) == dt

    def test_compilation(self, Article, session):
        query = sa.select([Article.created_at])
        # the type should be cacheable and not throw exception
        session.execute(query)
