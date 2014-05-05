import sqlalchemy as sa
from sqlalchemy_utils import get_referencing_foreign_keys
from tests import TestCase


class TestGetReferencingFksWithCompositeKeys(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)

        class Article(self.Base):
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

        self.User = User
        self.Article = Article

    def test_with_declarative_class(self):
        fks = get_referencing_foreign_keys(self.User)
        assert self.Article.__table__.foreign_keys == fks

    def test_with_table(self):
        fks = get_referencing_foreign_keys(self.User.__table__)
        assert self.Article.__table__.foreign_keys == fks
