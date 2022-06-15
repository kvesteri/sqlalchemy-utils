import pytest
import sqlalchemy as sa

from sqlalchemy_utils import dependent_objects, get_referencing_foreign_keys


class TestDependentObjects:

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))
        return User

    @pytest.fixture
    def Article(self, Base, User):
        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
            owner_id = sa.Column(
                sa.Integer, sa.ForeignKey('user.id', ondelete='SET NULL')
            )

            author = sa.orm.relationship(User, foreign_keys=[author_id])
            owner = sa.orm.relationship(User, foreign_keys=[owner_id])
        return Article

    @pytest.fixture
    def BlogPost(self, Base, User):
        class BlogPost(Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            owner_id = sa.Column(
                sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE')
            )

            owner = sa.orm.relationship(User)
        return BlogPost

    @pytest.fixture
    def init_models(self, User, Article, BlogPost):
        pass

    def test_returns_all_dependent_objects(self, session, User, Article):
        user = User(first_name='John')
        articles = [
            Article(author=user),
            Article(),
            Article(owner=user),
            Article(author=user, owner=user)
        ]
        session.add_all(articles)
        session.commit()

        deps = list(dependent_objects(user))
        assert len(deps) == 3
        assert articles[0] in deps
        assert articles[2] in deps
        assert articles[3] in deps

    def test_with_foreign_keys_parameter(
        self,
        session,
        User,
        Article,
        BlogPost
    ):
        user = User(first_name='John')
        objects = [
            Article(author=user),
            Article(),
            Article(owner=user),
            Article(author=user, owner=user),
            BlogPost(owner=user)
        ]
        session.add_all(objects)
        session.commit()

        deps = list(
            dependent_objects(
                user,
                (
                    fk for fk in get_referencing_foreign_keys(User)
                    if fk.ondelete == 'RESTRICT' or fk.ondelete is None
                )
            ).limit(5)
        )
        assert len(deps) == 2
        assert objects[0] in deps
        assert objects[3] in deps


class TestDependentObjectsWithColumnAliases:

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))
        return User

    @pytest.fixture
    def Article(self, Base, User):
        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(
                '_author_id', sa.Integer, sa.ForeignKey('user.id')
            )
            owner_id = sa.Column(
                '_owner_id',
                sa.Integer, sa.ForeignKey('user.id', ondelete='SET NULL')
            )

            author = sa.orm.relationship(User, foreign_keys=[author_id])
            owner = sa.orm.relationship(User, foreign_keys=[owner_id])
        return Article

    @pytest.fixture
    def BlogPost(self, Base, User):
        class BlogPost(Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            owner_id = sa.Column(
                '_owner_id',
                sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE')
            )

            owner = sa.orm.relationship(User)
        return BlogPost

    @pytest.fixture
    def init_models(self, User, Article, BlogPost):
        pass

    def test_returns_all_dependent_objects(self, session, User, Article):
        user = User(first_name='John')
        articles = [
            Article(author=user),
            Article(),
            Article(owner=user),
            Article(author=user, owner=user)
        ]
        session.add_all(articles)
        session.commit()

        deps = list(dependent_objects(user))
        assert len(deps) == 3
        assert articles[0] in deps
        assert articles[2] in deps
        assert articles[3] in deps

    def test_with_foreign_keys_parameter(
        self,
        session,
        User,
        Article,
        BlogPost
    ):
        user = User(first_name='John')
        objects = [
            Article(author=user),
            Article(),
            Article(owner=user),
            Article(author=user, owner=user),
            BlogPost(owner=user)
        ]
        session.add_all(objects)
        session.commit()

        deps = list(
            dependent_objects(
                user,
                (
                    fk for fk in get_referencing_foreign_keys(User)
                    if fk.ondelete == 'RESTRICT' or fk.ondelete is None
                )
            ).limit(5)
        )
        assert len(deps) == 2
        assert objects[0] in deps
        assert objects[3] in deps


class TestDependentObjectsWithManyReferences:

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))
        return User

    @pytest.fixture
    def BlogPost(self, Base, User):
        class BlogPost(Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
            author = sa.orm.relationship(User)
        return BlogPost

    @pytest.fixture
    def Article(self, Base, User):
        class Article(Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
            author = sa.orm.relationship(User)
        return Article

    @pytest.fixture
    def init_models(self, User, BlogPost, Article):
        pass

    def test_with_many_dependencies(self, session, User, Article, BlogPost):
        user = User(first_name='John')
        objects = [
            Article(author=user),
            BlogPost(author=user)
        ]
        session.add_all(objects)
        session.commit()
        deps = list(dependent_objects(user))
        assert len(deps) == 2


class TestDependentObjectsWithCompositeKeys:

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

            author = sa.orm.relationship(User)
        return Article

    @pytest.fixture
    def init_models(self, User, Article):
        pass

    def test_returns_all_dependent_objects(self, session, User, Article):
        user = User(first_name='John', last_name='Smith')
        articles = [
            Article(author=user),
            Article(),
            Article(),
            Article(author=user)
        ]
        session.add_all(articles)
        session.commit()

        deps = list(dependent_objects(user))
        assert len(deps) == 2
        assert articles[0] in deps
        assert articles[3] in deps


class TestDependentObjectsWithSingleTableInheritance:

    @pytest.fixture
    def Category(self, Base):
        class Category(Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return Category

    @pytest.fixture
    def TextItem(self, Base, Category):
        class TextItem(Base):
            __tablename__ = 'text_item'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            category_id = sa.Column(
                sa.Integer,
                sa.ForeignKey(Category.id)
            )
            category = sa.orm.relationship(
                Category,
                backref=sa.orm.backref(
                    'articles'
                )
            )
            type = sa.Column(sa.Unicode(255))

            __mapper_args__ = {
                'polymorphic_on': type,
            }
        return TextItem

    @pytest.fixture
    def Article(self, TextItem):
        class Article(TextItem):
            __mapper_args__ = {
                'polymorphic_identity': 'article'
            }
        return Article

    @pytest.fixture
    def BlogPost(self, TextItem):
        class BlogPost(TextItem):
            __mapper_args__ = {
                'polymorphic_identity': 'blog_post'
            }
        return BlogPost

    @pytest.fixture
    def init_models(self, Category, TextItem, Article, BlogPost):
        pass

    def test_returns_all_dependent_objects(self, session, Category, Article):
        category1 = Category(name='Category #1')
        category2 = Category(name='Category #2')
        articles = [
            Article(category=category1),
            Article(category=category1),
            Article(category=category2),
            Article(category=category2),
        ]
        session.add_all(articles)
        session.commit()

        deps = list(dependent_objects(category1))
        assert len(deps) == 2
        assert articles[0] in deps
        assert articles[1] in deps
