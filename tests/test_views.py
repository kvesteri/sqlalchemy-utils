import pytest
import sqlalchemy as sa

from sqlalchemy_utils import (
    create_materialized_view,
    create_view,
    refresh_materialized_view
)


@pytest.fixture
def Article(Base, User):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        author_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
        author = sa.orm.relationship(User)
    return Article


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
    return User


@pytest.fixture
def ArticleMV(Base, Article, User):
    class ArticleMV(Base):
        __table__ = create_materialized_view(
            name='article_mv',
            selectable=sa.select(
                [
                    Article.id,
                    Article.name,
                    User.id.label('author_id'),
                    User.name.label('author_name')
                ],
                from_obj=(
                    Article.__table__
                    .join(User, Article.author_id == User.id)
                )
            ),
            metadata=Base.metadata,
            indexes=[sa.Index('article_mv_id_idx', 'id')]
        )
    return ArticleMV


@pytest.fixture
def ArticleView(Base, Article, User):
    class ArticleView(Base):
        __table__ = create_view(
            name='article_view',
            selectable=sa.select(
                [
                    Article.id,
                    Article.name,
                    User.id.label('author_id'),
                    User.name.label('author_name')
                ],
                from_obj=(
                    Article.__table__
                    .join(User, Article.author_id == User.id)
                )
            ),
            metadata=Base.metadata
        )
    return ArticleView


@pytest.fixture
def init_models(ArticleMV, ArticleView):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestMaterializedViews:
    def test_refresh_materialized_view(
        self,
        session,
        Article,
        User,
        ArticleMV
    ):
        article = Article(
            name='Some article',
            author=User(name='Some user')
        )
        session.add(article)
        session.commit()
        refresh_materialized_view(session, 'article_mv')
        materialized = session.query(ArticleMV).first()
        assert materialized.name == 'Some article'
        assert materialized.author_name == 'Some user'

    def test_querying_view(
        self,
        session,
        Article,
        User,
        ArticleView
    ):
        article = Article(
            name='Some article',
            author=User(name='Some user')
        )
        session.add(article)
        session.commit()
        row = session.query(ArticleView).first()
        assert row.name == 'Some article'
        assert row.author_name == 'Some user'
