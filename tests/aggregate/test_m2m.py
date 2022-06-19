import pytest
import sqlalchemy as sa

from sqlalchemy_utils.aggregates import aggregated


@pytest.fixture
def User(Base):
    user_group = sa.Table(
        'user_group',
        Base.metadata,
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id'))
    )

    class User(Base):
        __tablename__ = 'user'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated('groups', sa.Column(sa.Integer, default=0))
        def group_count(self):
            return sa.func.count('1')

        groups = sa.orm.relationship(
            'Group',
            backref='users',
            secondary=user_group
        )
    return User


@pytest.fixture
def Group(Base):
    class Group(Base):
        __tablename__ = 'group'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
    return Group


@pytest.fixture
def init_models(User, Group):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestAggregatesWithManyToManyRelationships:

    def test_assigns_aggregates_on_insert(self, session, User, Group):
        user = User(
            name='John Matrix'
        )
        session.add(user)
        session.commit()
        group = Group(
            name='Some group',
            users=[user]
        )
        session.add(group)
        session.commit()
        session.refresh(user)
        assert user.group_count == 1

    def test_updates_aggregates_on_delete(self, session, User, Group):
        user = User(
            name='John Matrix'
        )
        session.add(user)
        session.commit()
        group = Group(
            name='Some group',
            users=[user]
        )
        session.add(group)
        session.commit()
        session.refresh(user)
        user.groups = []
        session.commit()
        session.refresh(user)
        assert user.group_count == 0
