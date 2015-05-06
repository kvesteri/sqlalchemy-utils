from itertools import chain

import sqlalchemy as sa

from sqlalchemy_utils.functions import non_indexed_foreign_keys
from tests import TestCase


class TestFindNonIndexedForeignKeys(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Article(self.Base):
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

        self.User = User
        self.Category = Category
        self.Article = Article

    def test_finds_all_non_indexed_fks(self):
        fks = non_indexed_foreign_keys(self.Base.metadata, self.engine)
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
