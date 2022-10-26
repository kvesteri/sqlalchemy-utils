import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_referencing_foreign_keys


class TestGetReferencingFksWithCompositeKeys:

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)
        return User

    @pytest.fixture
    def Article(self, Base, User):
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
        return Article

    @pytest.fixture
    def init_models(self, User, Article):
        pass

    def test_with_declarative_class(self, User, Article):
        fks = get_referencing_foreign_keys(User)
        assert Article.__table__.foreign_keys == fks

    def test_with_table(self, User, Article):
        fks = get_referencing_foreign_keys(User.__table__)
        assert Article.__table__.foreign_keys == fks


class TestGetReferencingFksWithInheritance:

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            type = sa.Column(sa.Unicode)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))

            __mapper_args__ = {
                'polymorphic_on': 'type'
            }
        return User

    @pytest.fixture
    def Admin(self, User):
        class Admin(User):
            __tablename__ = 'admin'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(User.id), primary_key=True
            )
        return Admin

    @pytest.fixture
    def TextItem(self, Base, User):
        class TextItem(Base):
            __tablename__ = 'textitem'
            id = sa.Column(sa.Integer, primary_key=True)
            type = sa.Column(sa.Unicode)
            author_id = sa.Column(sa.Integer, sa.ForeignKey(User.id))
            __mapper_args__ = {
                'polymorphic_on': 'type'
            }
        return TextItem

    @pytest.fixture
    def Article(self, TextItem):
        class Article(TextItem):
            __tablename__ = 'article'
            id = sa.Column(
                sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
            )
            __mapper_args__ = {
                'polymorphic_identity': 'article'
            }
        return Article

    @pytest.fixture
    def init_models(self, User, Admin, TextItem, Article):
        pass

    def test_with_declarative_class(self, Admin, TextItem):
        fks = get_referencing_foreign_keys(Admin)
        assert TextItem.__table__.foreign_keys == fks

    def test_with_table(self, Admin):
        fks = get_referencing_foreign_keys(Admin.__table__)
        assert fks == set()
