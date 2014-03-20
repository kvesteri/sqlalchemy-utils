import sqlalchemy as sa
from tests import TestCase
from sqlalchemy_utils.functions import query_entities


class TestQueryEntities(TestCase):
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

    def test_simple_query(self):
        query = self.session.query(self.User)
        assert list(query_entities(query)) == [self.User]

    def test_column_entity(self):
        query = self.session.query(self.User.id)
        assert list(query_entities(query)) == [self.User]

    def test_column_entity_with_label(self):
        query = self.session.query(self.User.id.label('id'))
        assert list(query_entities(query)) == [self.User]

    def test_with_subquery(self):
        number_of_sales = (
            sa.select(
                [sa.func.count(self.Article.id)],
            )
            .select_from(
                self.Article.__table__
            )
        ).label('number_of_articles')

        query = self.session.query(self.User, number_of_sales)
        assert list(query_entities(query)) == [self.User]

    def test_mapper(self):
        query = self.session.query(self.User.__mapper__)
        assert list(query_entities(query)) == [self.User]

    def test_joins(self):
        query = self.session.query(self.User.__mapper__).join(self.Article)
        assert list(query_entities(query)) == [self.User, self.Article]

    def test_aliased_entity(self):
        query = self.session.query(sa.orm.aliased(self.User))
        assert list(query_entities(query)) == [self.User]
