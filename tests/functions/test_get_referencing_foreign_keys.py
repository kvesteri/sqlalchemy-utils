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


class TestGetReferencingFksWithInheritance(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            type = sa.Column(sa.Unicode)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))

            __mapper_args__ = {
                'polymorphic_on': 'type'
            }

        class Admin(User):
            __tablename__ = 'admin'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(User.id), primary_key=True
            )

        class TextItem(self.Base):
            __tablename__ = 'textitem'
            id = sa.Column(sa.Integer, primary_key=True)
            type = sa.Column(sa.Unicode)
            author_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
            __mapper_args__ = {
                'polymorphic_on': 'type'
            }

        class Article(TextItem):
            __tablename__ = 'article'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
            )
            __mapper_args__ = {
                'polymorphic_identity': 'article'
            }

        self.Admin = Admin
        self.User = User
        self.Article = Article
        self.TextItem = TextItem

    def test_with_declarative_class(self):
        fks = get_referencing_foreign_keys(self.Admin)
        assert self.TextItem.__table__.foreign_keys == fks

    def test_with_table(self):
        fks = get_referencing_foreign_keys(self.Admin.__table__)
        assert fks == set([])
