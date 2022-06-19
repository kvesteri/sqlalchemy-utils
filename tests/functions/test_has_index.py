import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_fk_constraint_for_columns, has_index


class TestHasIndex:

    @pytest.fixture
    def table(self, Base):
        class ArticleTranslation(Base):
            __tablename__ = 'article_translation'
            id = sa.Column(sa.Integer, primary_key=True)
            locale = sa.Column(sa.String(10), primary_key=True)
            title = sa.Column(sa.String(100))
            is_published = sa.Column(sa.Boolean, index=True)
            is_deleted = sa.Column(sa.Boolean)
            is_archived = sa.Column(sa.Boolean)

            __table_args__ = (
                sa.Index('my_index', is_deleted, is_archived),
            )
        return ArticleTranslation.__table__

    def test_column_that_belongs_to_an_alias(self, table):
        alias = sa.orm.aliased(table)
        with pytest.raises(TypeError):
            assert has_index(alias.c.id)

    def test_compound_primary_key(self, table):
        assert has_index(table.c.id)
        assert not has_index(table.c.locale)

    def test_single_column_index(self, table):
        assert has_index(table.c.is_published)

    def test_compound_column_index(self, table):
        assert has_index(table.c.is_deleted)
        assert not has_index(table.c.is_archived)

    def test_table_without_primary_key(self):
        article = sa.Table(
            'article',
            sa.MetaData(),
            sa.Column('name', sa.String)
        )
        assert not has_index(article.c.name)


class TestHasIndexWithFKConstraint:
    def test_composite_fk_without_index(self, Base):

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
        assert not has_index(constraint)

    def test_composite_fk_with_index(self, Base):

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
                    'my_index', author_first_name, author_last_name
                )
            )

        table = Article.__table__
        constraint = get_fk_constraint_for_columns(
            table,
            table.c.author_first_name,
            table.c.author_last_name
        )
        assert has_index(constraint)

    def test_composite_fk_with_partial_index_match(self, Base):

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
                    id
                )
            )

        table = Article.__table__
        constraint = get_fk_constraint_for_columns(
            table,
            table.c.author_first_name,
            table.c.author_last_name
        )
        assert has_index(constraint)
