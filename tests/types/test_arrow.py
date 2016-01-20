from datetime import datetime

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.types import arrow


@pytest.fixture
def Article(Base):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        created_at = sa.Column(arrow.ArrowType)
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
            created_at='1367900664'
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
        assert compiled == 'article.created_at > 2015-01-01'
