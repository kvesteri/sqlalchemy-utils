from itertools import chain

import pytest
import sqlalchemy as sa

from sqlalchemy_utils.functions import non_indexed_foreign_keys


class TestFindNonIndexedForeignKeys:

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return User

    @pytest.fixture
    def Category(self, Base):
        class Category(Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return Category

    @pytest.fixture
    def Article(self, Base, User, Category):
        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            author_id = sa.Column(
                sa.Integer, sa.ForeignKey(User.id), index=True
            )
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category,
                primaryjoin=category_id == Category.id,
                backref=sa.orm.backref(
                    'articles',
                )
            )
        return Article

    @pytest.fixture
    def init_models(self, User, Category, Article):
        pass

    def test_finds_all_non_indexed_fks(self, session, Base, engine):
        fks = non_indexed_foreign_keys(Base.metadata, engine)
        assert (
            'article' in
            fks
        )
        column_names = list(chain(
            *(
                names for names in (
                    fk.columns.keys()
                    for fk in fks['article']
                )
            )
        ))
        assert 'category_id' in column_names
        assert 'author_id' not in column_names
