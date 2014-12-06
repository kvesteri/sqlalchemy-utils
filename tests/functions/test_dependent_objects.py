import sqlalchemy as sa
from sqlalchemy_utils import dependent_objects, get_referencing_foreign_keys
from tests import TestCase


class TestDependentObjects(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
            owner_id = sa.Column(
                sa.Integer, sa.ForeignKey('user.id', ondelete='SET NULL')
            )

            author = sa.orm.relationship(User, foreign_keys=[author_id])
            owner = sa.orm.relationship(User, foreign_keys=[owner_id])

        class BlogPost(self.Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            owner_id = sa.Column(
                sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE')
            )

            owner = sa.orm.relationship(User)

        self.User = User
        self.Article = Article
        self.BlogPost = BlogPost

    def test_returns_all_dependent_objects(self):
        user = self.User(first_name=u'John')
        articles = [
            self.Article(author=user),
            self.Article(),
            self.Article(owner=user),
            self.Article(author=user, owner=user)
        ]
        self.session.add_all(articles)
        self.session.commit()

        deps = list(dependent_objects(user))
        assert len(deps) == 3
        assert articles[0] in deps
        assert articles[2] in deps
        assert articles[3] in deps

    def test_with_foreign_keys_parameter(self):
        user = self.User(first_name=u'John')
        objects = [
            self.Article(author=user),
            self.Article(),
            self.Article(owner=user),
            self.Article(author=user, owner=user),
            self.BlogPost(owner=user)
        ]
        self.session.add_all(objects)
        self.session.commit()

        deps = list(
            dependent_objects(
                user,
                (
                    fk for fk in get_referencing_foreign_keys(self.User)
                    if fk.ondelete == 'RESTRICT' or fk.ondelete is None
                )
            ).limit(5)
        )
        assert len(deps) == 2
        assert objects[0] in deps
        assert objects[3] in deps


class TestDependentObjectsWithColumnAliases(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))

        class Article(self.Base):
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

        class BlogPost(self.Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            owner_id = sa.Column(
                '_owner_id',
                sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE')
            )

            owner = sa.orm.relationship(User)

        self.User = User
        self.Article = Article
        self.BlogPost = BlogPost

    def test_returns_all_dependent_objects(self):
        user = self.User(first_name=u'John')
        articles = [
            self.Article(author=user),
            self.Article(),
            self.Article(owner=user),
            self.Article(author=user, owner=user)
        ]
        self.session.add_all(articles)
        self.session.commit()

        deps = list(dependent_objects(user))
        assert len(deps) == 3
        assert articles[0] in deps
        assert articles[2] in deps
        assert articles[3] in deps

    def test_with_foreign_keys_parameter(self):
        user = self.User(first_name=u'John')
        objects = [
            self.Article(author=user),
            self.Article(),
            self.Article(owner=user),
            self.Article(author=user, owner=user),
            self.BlogPost(owner=user)
        ]
        self.session.add_all(objects)
        self.session.commit()

        deps = list(
            dependent_objects(
                user,
                (
                    fk for fk in get_referencing_foreign_keys(self.User)
                    if fk.ondelete == 'RESTRICT' or fk.ondelete is None
                )
            ).limit(5)
        )
        assert len(deps) == 2
        assert objects[0] in deps
        assert objects[3] in deps


class TestDependentObjectsWithManyReferences(TestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            first_name = sa.Column(sa.Unicode(255))
            last_name = sa.Column(sa.Unicode(255))

        class BlogPost(self.Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
            author = sa.orm.relationship(User)

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
            author = sa.orm.relationship(User)

        self.User = User
        self.Article = Article
        self.BlogPost = BlogPost

    def test_with_many_dependencies(self):
        user = self.User(first_name=u'John')
        objects = [
            self.Article(author=user),
            self.BlogPost(author=user)
        ]
        self.session.add_all(objects)
        self.session.commit()
        deps = list(dependent_objects(user))
        assert len(deps) == 2


class TestDependentObjectsWithCompositeKeys(TestCase):
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

            author = sa.orm.relationship(User)

        self.User = User
        self.Article = Article

    def test_returns_all_dependent_objects(self):
        user = self.User(first_name=u'John', last_name=u'Smith')
        articles = [
            self.Article(author=user),
            self.Article(),
            self.Article(),
            self.Article(author=user)
        ]
        self.session.add_all(articles)
        self.session.commit()

        deps = list(dependent_objects(user))
        assert len(deps) == 2
        assert articles[0] in deps
        assert articles[3] in deps


class TestDependentObjectsWithSingleTableInheritance(TestCase):
    def create_models(self):
        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class TextItem(self.Base):
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

        class Article(TextItem):
            __mapper_args__ = {
                'polymorphic_identity': u'article'
            }

        class BlogPost(TextItem):
            __mapper_args__ = {
                'polymorphic_identity': u'blog_post'
            }

        self.Category = Category
        self.TextItem = TextItem
        self.Article = Article
        self.BlogPost = BlogPost

    def test_returns_all_dependent_objects(self):
        category1 = self.Category(name=u'Category #1')
        category2 = self.Category(name=u'Category #2')
        articles = [
            self.Article(category=category1),
            self.Article(category=category1),
            self.Article(category=category2),
            self.Article(category=category2),
        ]
        self.session.add_all(articles)
        self.session.commit()

        deps = list(dependent_objects(category1))
        assert len(deps) == 2
        assert articles[0] in deps
        assert articles[1] in deps
