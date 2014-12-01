import sqlalchemy as sa
from sqlalchemy_utils.aggregates import aggregated
from tests import TestCase


class TestAggregatesWithManyToManyRelationships(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        user_group = sa.Table('user_group', self.Base.metadata,
            sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
            sa.Column('group_id', sa.Integer, sa.ForeignKey('group.id'))
        )

        class User(self.Base):
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

        class Group(self.Base):
            __tablename__ = 'group'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        self.User = User
        self.Group = Group

    def test_assigns_aggregates_on_insert(self):
        user = self.User(
            name=u'John Matrix'
        )
        self.session.add(user)
        self.session.commit()
        group = self.Group(
            name=u'Some group',
            users=[user]
        )
        self.session.add(group)
        self.session.commit()
        self.session.refresh(user)
        assert user.group_count == 1

    def test_updates_aggregates_on_delete(self):
        user = self.User(
            name=u'John Matrix'
        )
        self.session.add(user)
        self.session.commit()
        group = self.Group(
            name=u'Some group',
            users=[user]
        )
        self.session.add(group)
        self.session.commit()
        self.session.refresh(user)
        user.groups = []
        self.session.commit()
        self.session.refresh(user)
        assert user.group_count == 0
