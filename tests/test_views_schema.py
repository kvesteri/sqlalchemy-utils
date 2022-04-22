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
def ArticleMV(Base, Article, User, engine):
    # def create_schema(engine):
    if not engine.dialect.has_schema(engine, 'main'):
        engine.execute(sa.schema.CreateSchema('main'))

    class ArticleMV(Base):
        __table__ = create_materialized_view(
            name='article-mv',
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
            aliases={'name': 'article_name'},
            metadata=Base.metadata,
            schema='main',
            indexes=[sa.Index('article-mv_id_idx', 'id')]
        )
        # __table_args__ = {"schema": "main"}
    return ArticleMV


@pytest.fixture
def ArticleView(Base, Article, User):
    class ArticleView(Base):
        __table__ = create_view(
            name='article-view',
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
            schema='main',
            metadata=Base.metadata
        )
        # __table_args__ = {"schema": "main"}

    return ArticleView


@pytest.fixture
def init_models(ArticleMV, ArticleView):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestMaterializedViews:

    # def create_schema(engine):
    #     if not engine.dialect.has_schema(engine, 'main'):
    #         engine.exeute(sa.schema.CreateSchema('main'))

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
        refresh_materialized_view(session, ArticleMV)
        materialized = session.query(ArticleMV).first()
        assert materialized.article_name == 'Some article'
        assert materialized.author_name == 'Some user'

    def test_querying_view(
        self,
        session,
        Article,
        User,
        # ArticleMV
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

    def drop_view(self, engine, ArticleMV, ArticleView):
        ArticleView.__table__.drop(engine)
        ArticleMV.__table__.drop(engine)
        if engine.dialect.has_schema(engine, 'main'):
            engine.execute(sa.schema.DropSchema('main'))


class TrivialViewTestCases:
    def life_cycle(
        self,
        engine,
        metadata,
        column,
        cascade_on_drop
    ):
        __table__ = create_view(
            name='trivial_view',
            selectable=sa.select([column]),
            metadata=metadata,
            cascade_on_drop=cascade_on_drop
        )
        __table__.create(engine)
        __table__.drop(engine)


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
        super(DoesntSupportCascade, self).test_life_cycle_cascade(
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


@pytest.mark.usefixtures('postgresql_dsn')
class TestPostgresTrivialView(SupportsCascade, SupportsNoCascade):
    pass


# @pytest.mark.usefixtures('mysql_dsn')
# class TestMySqlTrivialView(SupportsCascade, SupportsNoCascade):
#     pass
#
#
# @pytest.mark.usefixtures('sqlite_none_database_dsn')
# class TestSqliteTrivialView(DoesntSupportCascade, SupportsNoCascade):
#     pass
