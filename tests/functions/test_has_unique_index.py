import sqlalchemy as sa
from pytest import raises
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import get_fk_constraint_for_columns, has_unique_index


class TestHasUniqueIndex(object):
    def setup_method(self, method):
        Base = declarative_base()

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)

        class ArticleTranslation(Base):
            __tablename__ = 'article_translation'
            id = sa.Column(sa.Integer, primary_key=True)
            locale = sa.Column(sa.String(10), primary_key=True)
            title = sa.Column(sa.String(100))
            is_published = sa.Column(sa.Boolean, index=True)
            is_deleted = sa.Column(sa.Boolean, unique=True)
            is_archived = sa.Column(sa.Boolean)

            __table_args__ = (
                sa.Index('my_index', is_archived, is_published, unique=True),
            )

        self.articles = Article.__table__
        self.article_translations = ArticleTranslation.__table__

    def test_primary_key(self):
        assert has_unique_index(self.articles.c.id)

    def test_column_of_aliased_table(self):
        alias = sa.orm.aliased(self.articles)
        with raises(TypeError):
            assert has_unique_index(alias.c.id)

    def test_unique_index(self):
        assert has_unique_index(self.article_translations.c.is_deleted)

    def test_compound_primary_key(self):
        assert not has_unique_index(self.article_translations.c.id)
        assert not has_unique_index(self.article_translations.c.locale)

    def test_single_column_index(self):
        assert not has_unique_index(self.article_translations.c.is_published)

    def test_compound_column_unique_index(self):
        assert not has_unique_index(self.article_translations.c.is_published)
        assert not has_unique_index(self.article_translations.c.is_archived)


class TestHasUniqueIndexWithFKConstraint(object):
    def test_composite_fk_without_index(self):
        Base = declarative_base()

        class User(Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_first_name = sa.Column(sa.Unicode(255))
            author_last_name = sa.Column(sa.Unicode(255))
            __table_args__ = (
                sa.ForeignKeyConstraint(
                    [author_first_name, author_last_name],
                    [User.first_name, User.last_name]
                ),
            )

        table = Article.__table__
        constraint = get_fk_constraint_for_columns(
            table,
            table.c.author_first_name,
            table.c.author_last_name
        )
        assert not has_unique_index(constraint)

    def test_composite_fk_with_index(self):
        Base = declarative_base()

        class User(Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_first_name = sa.Column(sa.Unicode(255))
            author_last_name = sa.Column(sa.Unicode(255))
            __table_args__ = (
                sa.ForeignKeyConstraint(
                    [author_first_name, author_last_name],
                    [User.first_name, User.last_name]
                ),
                sa.Index(
                    'my_index',
                    author_first_name,
                    author_last_name,
                    unique=True
                )
            )

        table = Article.__table__
        constraint = get_fk_constraint_for_columns(
            table,
            table.c.author_first_name,
            table.c.author_last_name
        )
        assert has_unique_index(constraint)

    def test_composite_fk_with_partial_index_match(self):
        Base = declarative_base()

        class User(Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)

        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_first_name = sa.Column(sa.Unicode(255))
            author_last_name = sa.Column(sa.Unicode(255))
            __table_args__ = (
                sa.ForeignKeyConstraint(
                    [author_first_name, author_last_name],
                    [User.first_name, User.last_name]
                ),
                sa.Index(
                    'my_index',
                    author_first_name,
                    author_last_name,
                    id,
                    unique=True
                )
            )

        table = Article.__table__
        constraint = get_fk_constraint_for_columns(
            table,
            table.c.author_first_name,
            table.c.author_last_name
        )
        assert not has_unique_index(constraint)
