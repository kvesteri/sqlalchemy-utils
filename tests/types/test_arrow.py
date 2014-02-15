from datetime import datetime
from pytest import mark
import sqlalchemy as sa
from sqlalchemy_utils.types import arrow
from tests import TestCase


@mark.skipif('arrow.arrow is None')
class TestArrowDateTimeType(TestCase):
    def create_models(self):
        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            created_at = sa.Column(arrow.ArrowType)

        self.Article = Article

    def test_parameter_processing(self):
        article = self.Article(
            created_at=arrow.arrow.get(datetime(2000, 11, 1))
        )

        self.session.add(article)
        self.session.commit()

        article = self.session.query(self.Article).first()
        assert article.created_at.datetime

    def test_string_coercion(self):
        article = self.Article(
            created_at='1367900664'
        )
        assert article.created_at.year == 2013

    def test_utc(self):
        time = arrow.arrow.utcnow()
        article = self.Article(created_at=time)
        self.session.add(article)
        assert article.created_at == time
        self.session.commit()
        assert article.created_at == time

    def test_other_tz(self):
        time = arrow.arrow.utcnow()
        local = time.to('US/Pacific')
        article = self.Article(created_at=local)
        self.session.add(article)
        assert article.created_at == time == local
        self.session.commit()
        assert article.created_at == time
