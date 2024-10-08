import pytest
import sqlalchemy as sa
import sqlalchemy.orm

from sqlalchemy_utils import (
    create_materialized_view,
    create_view,
    refresh_materialized_view
)
from sqlalchemy_utils.view import CreateView


@pytest.fixture
def Article(Base, User):
    class Article(Base):
        __tablename__ = 'article'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(128))
        author_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
        author = sa.orm.relationship(User)
    return Article


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(128))
    return User


@pytest.fixture
def ArticleMV(Base, Article, User):
    class ArticleMV(Base):
        __table__ = create_materialized_view(
            name='article-mv',
            selectable=sa.select(
                Article.id,
                Article.name,
                User.id.label('author_id'),
                User.name.label('author_name'),
            ).select_from(
                Article.__table__.join(User, Article.author_id == User.id)
            ),
            aliases={'name': 'article_name'},
            metadata=Base.metadata,
            indexes=[sa.Index('article-mv_id_idx', 'id')]
        )
    return ArticleMV


@pytest.fixture
def ArticleView(Base, Article, User):
    class ArticleView(Base):
        __table__ = create_view(
            name='article-view',
            selectable=sa.select(
                Article.id,
                Article.name,
                User.id.label('author_id'),
                User.name.label('author_name'),
            ).select_from(
                Article.__table__.join(User, Article.author_id == User.id)
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
        refresh_materialized_view(session, 'article-mv')
        materialized = session.query(ArticleMV).first()
        assert materialized.article_name == 'Some article'
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


class TrivialViewTestCases:
    def life_cycle(
        self,
        engine,
        metadata,
        column,
        cascade_on_drop,
        replace=False,
    ):
        create_view(
            name='trivial_view',
            selectable=sa.select(column),
            metadata=metadata,
            cascade_on_drop=cascade_on_drop,
            replace=replace,
        )
        metadata.create_all(engine)
        metadata.drop_all(engine)


class SupportsCascade(TrivialViewTestCases):
    def test_life_cycle_cascade(
        self,
        connection,
        engine,
        Base,
        User
    ):
        self.life_cycle(engine, Base.metadata, User.id, cascade_on_drop=True)


class DoesntSupportCascade(SupportsCascade):
    @pytest.mark.xfail
    def test_life_cycle_cascade(self, *args, **kwargs):
        super().test_life_cycle_cascade(
            *args,
            **kwargs
        )


class SupportsNoCascade(TrivialViewTestCases):
    def test_life_cycle_no_cascade(
        self,
        connection,
        engine,
        Base,
        User
    ):
        self.life_cycle(engine, Base.metadata, User.id, cascade_on_drop=False)


class SupportsReplace(TrivialViewTestCases):
    def test_life_cycle_replace(
        self,
        connection,
        engine,
        Base,
        User
    ):
        self.life_cycle(
            engine,
            Base.metadata,
            User.id,
            cascade_on_drop=False,
            replace=True,
        )

    def test_life_cycle_replace_existing(
        self,
        connection,
        engine,
        Base,
        User
    ):
        create_view(
            name='trivial_view',
            selectable=sa.select(User.id),
            metadata=Base.metadata,
        )
        Base.metadata.create_all(engine)
        view = CreateView(
            name='trivial_view',
            selectable=sa.select(User.id),
            replace=True,
        )
        with connection.begin():
            connection.execute(view)
        Base.metadata.drop_all(engine)

    def test_replace_materialized(
        self,
        connection,
        engine,
        Base,
        User
    ):
        with pytest.raises(ValueError):
            CreateView(
                name='trivial_view',
                selectable=sa.select(User.id),
                materialized=True,
                replace=True,
            )


@pytest.mark.usefixtures('postgresql_dsn')
class TestPostgresTrivialView(SupportsCascade, SupportsNoCascade, SupportsReplace):
    pass


@pytest.mark.usefixtures('mysql_dsn')
class TestMySqlTrivialView(SupportsCascade, SupportsNoCascade, SupportsReplace):
    pass


@pytest.mark.usefixtures('sqlite_none_database_dsn')
class TestSqliteTrivialView(DoesntSupportCascade, SupportsNoCascade):
    pass
