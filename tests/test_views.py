import pytest
import sqlalchemy as sa

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
            indexes=[sa.Index('article-mv_id_idx', 'id')]
        )
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
            metadata=Base.metadata
        )
    return ArticleView


@pytest.fixture
def Booking(Base, Person):
    class Booking(Base):
        __tablename__ = "booking"
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        person_id = sa.Column(sa.Integer, sa.ForeignKey(Person.id))
        person = sa.orm.relationship(Person)

    return Booking


@pytest.fixture
def Person(Base):
    class Person(Base):
        __tablename__ = "person"
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)

    return Person


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

    def create_view(
        self,
        Booking,
        Person,
        if_not_exists=None,
        or_replace=None,
        materialized=None,
    ):
        return CreateView(
            name="booking-view",
            selectable=sa.select(
                [
                    Booking.id,
                    Booking.name,
                    Person.id.label('person_id'),
                    Person.name.label('person_name'),
                ],
                from_obj=(Booking.__table__.join(
                    Person, Booking.person_id == Person.id)),
            ),
            materialized=materialized,
            if_not_exists=if_not_exists,
            or_replace=or_replace,
        )


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


class SupportCreateViewIfNotExists(TrivialViewTestCases):
    def test_create_view_if_not_exists(self, engine, Booking, Person):
        view = self.create_view(Booking, Person, if_not_exists=True)
        expected = (
            'CREATE VIEW IF NOT EXISTS "booking-view" AS SELECT booking.id, '
            'booking.name, person.id AS person_id, person.name AS person_name '
            '\nFROM booking JOIN person ON booking.person_id = person.id'
        )
        assert str(view.compile(dialect=engine.dialect)) == expected


class SupportCreateOrReplaceView(TrivialViewTestCases):
    def test_create_or_replace_view(self, engine, Booking, Person):
        view = self.create_view(Booking, Person, or_replace=True)
        expected = (
            'CREATE OR REPLACE VIEW "booking-view" AS SELECT booking.id, '
            'booking.name, person.id AS person_id, person.name AS person_name '
            '\nFROM booking JOIN person ON booking.person_id = person.id'
        )
        assert str(view.compile(dialect=engine.dialect)) == expected


class SupportCreateMaterializedViewIfNotExists(TrivialViewTestCases):
    def test_create_materialized_view_if_not_exists(
        self, engine, Booking, Person,
    ):
        view = self.create_view(
            Booking, Person, if_not_exists=True, materialized=True)
        expected = (
            'CREATE MATERIALIZED VIEW IF NOT EXISTS "booking-view" AS SELECT '
            'booking.id, booking.name, person.id AS person_id, '
            'person.name AS person_name \n'
            'FROM booking JOIN person ON booking.person_id = person.id'
        )
        assert str(view.compile(dialect=engine.dialect)) == expected


class SupportCreateOrReplaceMaterializedView(TrivialViewTestCases):
    def test_create_or_replace_materialized_view(
        self, engine, Booking, Person,
    ):
        view = self.create_view(
            Booking, Person, or_replace=True, materialized=True)
        expected = (
            'CREATE OR REPLACE MATERIALIZED VIEW "booking-view" AS SELECT '
            'booking.id, booking.name, person.id AS person_id, '
            'person.name AS person_name \n'
            'FROM booking JOIN person ON booking.person_id = person.id'
        )
        assert str(view.compile(dialect=engine.dialect)) == expected


class DoesNotSupportCreateViewIfNotExists(TrivialViewTestCases):
    def test_create_view_if_not_exists(self, engine, Booking, Person):
        view = self.create_view(Booking, Person, if_not_exists=True)
        expected = (
            'CREATE VIEW "booking-view" AS SELECT booking.id, booking.name, '
            'person.id AS person_id, person.name AS person_name \n'
            'FROM booking JOIN person ON booking.person_id = person.id'
        )
        assert str(view.compile(dialect=engine.dialect)) == expected


class DoesNotSupportCreateOrReplaceMaterializedView(TrivialViewTestCases):
    def test_create_or_replace_materialized_view(
        self, engine, Booking, Person,
    ):
        view = self.create_view(
            Booking, Person, or_replace=True, materialized=True)
        expected = (
            'CREATE MATERIALIZED VIEW "booking-view" AS SELECT booking.id, '
            'booking.name, '
            'person.id AS person_id, person.name AS person_name \n'
            'FROM booking JOIN person ON booking.person_id = person.id'
        )
        assert str(view.compile(dialect=engine.dialect)) == expected


class TestGenericDbTrivialView(
    SupportCreateViewIfNotExists,
    SupportCreateOrReplaceView,
    SupportCreateMaterializedViewIfNotExists,
    SupportCreateOrReplaceMaterializedView
):
    ...


@pytest.mark.usefixtures('postgresql_dsn')
class TestPostgresTrivialView(
    SupportsCascade,
    SupportsNoCascade,
    SupportCreateOrReplaceView,
    SupportCreateMaterializedViewIfNotExists,
    DoesNotSupportCreateViewIfNotExists,
    DoesNotSupportCreateOrReplaceMaterializedView,
):
    pass


@pytest.mark.usefixtures('mysql_dsn')
class TestMySqlTrivialView(SupportsCascade, SupportsNoCascade):
    pass


@pytest.mark.usefixtures('sqlite_none_database_dsn')
class TestSqliteTrivialView(DoesntSupportCascade, SupportsNoCascade):
    pass
