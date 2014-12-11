import sqlalchemy as sa

from sqlalchemy_utils.functions.sort_query import make_order_by_deterministic

from tests import assert_contains, TestCase


class TestMakeOrderByDeterministic(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode)
            email = sa.Column(sa.Unicode, unique=True)

            email_lower = sa.orm.column_property(
                sa.func.lower(name)
            )

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
            author = sa.orm.relationship(User)

        User.article_count = sa.orm.column_property(
            sa.select([sa.func.count()], from_obj=Article)
            .where(Article.author_id == User.id)
            .label('article_count')
        )

        self.User = User
        self.Article = Article

    def test_column_property(self):
        query = self.session.query(self.User).order_by(self.User.email_lower)
        query = make_order_by_deterministic(query)
        assert_contains('lower("user".name), "user".id ASC', query)

    def test_unique_column(self):
        query = self.session.query(self.User).order_by(self.User.email)
        query = make_order_by_deterministic(query)

        assert str(query).endswith('ORDER BY "user".email')

    def test_non_unique_column(self):
        query = self.session.query(self.User).order_by(self.User.name)
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY "user".name, "user".id ASC', query)

    def test_descending_order_by(self):
        query = self.session.query(self.User).order_by(
            sa.desc(self.User.name)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY "user".name DESC, "user".id DESC', query)

    def test_ascending_order_by(self):
        query = self.session.query(self.User).order_by(
            sa.asc(self.User.name)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY "user".name ASC, "user".id ASC', query)

    def test_string_order_by(self):
        query = self.session.query(self.User).order_by('name')
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY name, "user".id ASC', query)

    def test_annotated_label(self):
        query = self.session.query(self.User).order_by(self.User.article_count)
        query = make_order_by_deterministic(query)
        assert_contains('article_count, "user".id ASC', query)

    def test_annotated_label_with_descending_order(self):
        query = self.session.query(self.User).order_by(
            sa.desc(self.User.article_count)
        )
        query = make_order_by_deterministic(query)
        assert_contains('ORDER BY article_count DESC, "user".id DESC', query)

    def test_query_without_order_by(self):
        query = self.session.query(self.User)
        query = make_order_by_deterministic(query)
        assert 'ORDER BY "user".id' in str(query)

    def test_alias(self):
        alias = sa.orm.aliased(self.User.__table__)
        query = self.session.query(alias).order_by(alias.c.name)
        query = make_order_by_deterministic(query)
        assert str(query).endswith('ORDER BY user_1.name, "user".id ASC')
