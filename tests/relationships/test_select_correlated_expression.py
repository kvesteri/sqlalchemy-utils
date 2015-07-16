import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker

from sqlalchemy_utils.relationships import select_correlated_expression


@pytest.fixture(scope='class')
def base():
    return declarative_base()


@pytest.fixture(scope='class')
def group_user_cls(base):
    return sa.Table(
        'group_user',
        base.metadata,
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id'))
    )


@pytest.fixture(scope='class')
def group_cls(base):
    class Group(base):
        __tablename__ = 'group'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)

    return Group


@pytest.fixture(scope='class')
def friendship_cls(base):
    return sa.Table(
        'friendships',
        base.metadata,
        sa.Column(
            'friend_a_id',
            sa.Integer,
            sa.ForeignKey('user.id'),
            primary_key=True
        ),
        sa.Column(
            'friend_b_id',
            sa.Integer,
            sa.ForeignKey('user.id'),
            primary_key=True
        )
    )


@pytest.fixture(scope='class')
def user_cls(base, group_user_cls, friendship_cls):
    class User(base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        groups = sa.orm.relationship(
            'Group',
            secondary=group_user_cls,
            backref='users'
        )

        # this relationship is used for persistence
        friends = sa.orm.relationship(
            'User',
            secondary=friendship_cls,
            primaryjoin=id == friendship_cls.c.friend_a_id,
            secondaryjoin=id == friendship_cls.c.friend_b_id,
        )

    friendship_union = sa.select([
        friendship_cls.c.friend_a_id,
        friendship_cls.c.friend_b_id
        ]).union(
            sa.select([
                friendship_cls.c.friend_b_id,
                friendship_cls.c.friend_a_id]
            )
    ).alias()

    User.all_friends = sa.orm.relationship(
        'User',
        secondary=friendship_union,
        primaryjoin=User.id == friendship_union.c.friend_a_id,
        secondaryjoin=User.id == friendship_union.c.friend_b_id,
        viewonly=True,
        order_by=User.id
    )
    return User


@pytest.fixture(scope='class')
def category_cls(base, group_user_cls, friendship_cls):
    class Category(base):
        __tablename__ = 'category'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        created_at = sa.Column(sa.DateTime)
        parent_id = sa.Column(sa.Integer, sa.ForeignKey('category.id'))
        parent = sa.orm.relationship(
            'Category',
            backref='subcategories',
            remote_side=[id],
            order_by=id
        )
    return Category


@pytest.fixture(scope='class')
def article_cls(base, category_cls, user_cls):
    class Article(base):
        __tablename__ = 'article'
        id = sa.Column('_id', sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        name_synonym = sa.orm.synonym('name')

        @hybrid_property
        def name_upper(self):
            return self.name.upper() if self.name else None

        @name_upper.expression
        def name_upper(cls):
            return sa.func.upper(cls.name)

        content = sa.Column(sa.String)

        category_id = sa.Column(sa.Integer, sa.ForeignKey(category_cls.id))
        category = sa.orm.relationship(category_cls, backref='articles')

        author_id = sa.Column(sa.Integer, sa.ForeignKey(user_cls.id))
        author = sa.orm.relationship(
            user_cls,
            primaryjoin=author_id == user_cls.id,
            backref='authored_articles'
        )

        owner_id = sa.Column(sa.Integer, sa.ForeignKey(user_cls.id))
        owner = sa.orm.relationship(
            user_cls,
            primaryjoin=owner_id == user_cls.id,
            backref='owned_articles'
        )
    return Article


@pytest.fixture(scope='class')
def comment_cls(base, article_cls, user_cls):
    class Comment(base):
        __tablename__ = 'comment'
        id = sa.Column(sa.Integer, primary_key=True)
        content = sa.Column(sa.String)
        article_id = sa.Column(sa.Integer, sa.ForeignKey(article_cls.id))
        article = sa.orm.relationship(article_cls, backref='comments')

        author_id = sa.Column(sa.Integer, sa.ForeignKey(user_cls.id))
        author = sa.orm.relationship(user_cls, backref='comments')

    article_cls.comment_count = sa.orm.column_property(
        sa.select([sa.func.count(Comment.id)])
        .where(Comment.article_id == article_cls.id)
        .correlate_except(article_cls)
    )

    return Comment


@pytest.fixture(scope='class')
def composite_pk_cls(base):
    class CompositePKModel(base):
        __tablename__ = 'composite_pk_model'
        a = sa.Column(sa.Integer, primary_key=True)
        b = sa.Column(sa.Integer, primary_key=True)
    return CompositePKModel


@pytest.fixture(scope='class')
def dns():
    return 'postgres://postgres@localhost/sqlalchemy_utils_test'


@pytest.yield_fixture(scope='class')
def engine(dns):
    engine = create_engine(dns)
    engine.echo = True
    yield engine
    engine.dispose()


@pytest.yield_fixture(scope='class')
def connection(engine):
    conn = engine.connect()
    yield conn
    conn.close()


@pytest.fixture(scope='class')
def model_mapping(article_cls, category_cls, comment_cls, group_cls, user_cls):
    return {
        'articles': article_cls,
        'categories': category_cls,
        'comments': comment_cls,
        'groups': group_cls,
        'users': user_cls
    }


@pytest.yield_fixture(scope='class')
def table_creator(base, connection, model_mapping):
    sa.orm.configure_mappers()
    base.metadata.create_all(connection)
    yield
    base.metadata.drop_all(connection)


@pytest.yield_fixture(scope='class')
def session(connection):
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close_all()


@pytest.fixture(scope='class')
def dataset(
    session,
    user_cls,
    group_cls,
    article_cls,
    category_cls,
    comment_cls
):
    group = group_cls(name='Group 1')
    group2 = group_cls(name='Group 2')
    user = user_cls(id=1, name='User 1', groups=[group, group2])
    user2 = user_cls(id=2, name='User 2')
    user3 = user_cls(id=3, name='User 3', groups=[group])
    user4 = user_cls(id=4, name='User 4', groups=[group2])
    user5 = user_cls(id=5, name='User 5')

    user.friends = [user2]
    user2.friends = [user3, user4]
    user3.friends = [user5]

    article = article_cls(
        name='Some article',
        author=user,
        owner=user2,
        category=category_cls(
            id=1,
            name='Some category',
            subcategories=[
                category_cls(
                    id=2,
                    name='Subcategory 1',
                    subcategories=[
                        category_cls(
                            id=3,
                            name='Subsubcategory 1',
                            subcategories=[
                                category_cls(
                                    id=5,
                                    name='Subsubsubcategory 1',
                                ),
                                category_cls(
                                    id=6,
                                    name='Subsubsubcategory 2',
                                )
                            ]
                        )
                    ]
                ),
                category_cls(id=4, name='Subcategory 2'),
            ]
        ),
        comments=[
            comment_cls(
                content='Some comment',
                author=user
            )
        ]
    )
    session.add(user3)
    session.add(user4)
    session.add(article)
    session.commit()


@pytest.mark.usefixtures('table_creator', 'dataset')
class TestSelectCorrelatedExpression(object):
    @pytest.mark.parametrize(
        ('model_key', 'related_model_key', 'path', 'result'),
        (
            (
                'categories',
                'categories',
                'subcategories',
                [
                    (1, 2),
                    (2, 1),
                    (3, 2),
                    (4, 0),
                    (5, 0),
                    (6, 0)
                ]
            ),
            (
                'articles',
                'comments',
                'comments',
                [
                    (1, 1),
                ]
            ),
            (
                'users',
                'groups',
                'groups',
                [
                    (1, 2),
                    (2, 0),
                    (3, 1),
                    (4, 1),
                    (5, 0)
                ]
            ),
            (
                'users',
                'users',
                'all_friends',
                [
                    (1, 1),
                    (2, 3),
                    (3, 2),
                    (4, 1),
                    (5, 1)
                ]
            ),
            (
                'users',
                'users',
                'all_friends.all_friends',
                [
                    (1, 3),
                    (2, 2),
                    (3, 3),
                    (4, 3),
                    (5, 2)
                ]
            ),
            (
                'users',
                'users',
                'groups.users',
                [
                    (1, 3),
                    (2, 0),
                    (3, 2),
                    (4, 2),
                    (5, 0)
                ]
            ),
            (
                'groups',
                'articles',
                'users.authored_articles',
                [
                    (1, 1),
                    (2, 1),
                ]
            ),
            (
                'categories',
                'categories',
                'subcategories.subcategories',
                [
                    (1, 1),
                    (2, 2),
                    (3, 0),
                    (4, 0),
                    (5, 0),
                    (6, 0)
                ]
            ),
            (
                'categories',
                'categories',
                'subcategories.subcategories.subcategories',
                [
                    (1, 2),
                    (2, 0),
                    (3, 0),
                    (4, 0),
                    (5, 0),
                    (6, 0)
                ]
            ),
        )
    )
    def test_returns_correct_results(
        self,
        session,
        model_mapping,
        model_key,
        related_model_key,
        path,
        result
    ):
        model = model_mapping[model_key]
        alias = sa.orm.aliased(model_mapping[related_model_key])
        aggregate = select_correlated_expression(
            model,
            sa.func.count(sa.distinct(alias.id)),
            path,
            alias
        )

        query = session.query(
            model.id,
            aggregate.label('count')
        ).order_by(model.id)
        assert query.all() == result

    def test_with_non_aggregate_function(
        self,
        session,
        user_cls,
        article_cls
    ):
        aggregate = select_correlated_expression(
            article_cls,
            sa.func.json_build_object('name', user_cls.name),
            'comments.author',
            user_cls
        )

        query = session.query(
            article_cls.id,
            aggregate.label('author_json')
        ).order_by(article_cls.id)
        result = query.all()
        assert result == [
            (1, {'name': 'User 1'})
        ]
