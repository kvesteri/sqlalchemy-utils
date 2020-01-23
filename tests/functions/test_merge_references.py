import pytest
import sqlalchemy as sa

from sqlalchemy_utils import merge_references


class TestMergeReferences(object):

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            def __repr__(self):
                return 'User(%r)' % self.name
        return User

    @pytest.fixture
    def BlogPost(self, Base, User):
        class BlogPost(Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            title = sa.Column(sa.Unicode(255))
            content = sa.Column(sa.UnicodeText)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

            author = sa.orm.relationship(User)
        return BlogPost

    @pytest.fixture
    def Address(self, Base, User):
        class Address(Base):
            __tablename__ = 'address'
            id = sa.Column(sa.Integer, primary_key=True)
            city = sa.Column(sa.UnicodeText)
            user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

            user = sa.orm.relationship(User)
        return Address

    @pytest.fixture
    def Comment(self, Base, User, BlogPost):
        class Comment(Base):
            __tablename__ = 'comment'
            id = sa.Column(sa.Integer, primary_key=True)
            content = sa.Column(sa.UnicodeText)
            blog_post_id = sa.Column(sa.Integer, sa.ForeignKey('blog_post.id'))
            user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

            blog_post = sa.orm.relationship(BlogPost)
            user = sa.orm.relationship(User)
        return Comment

    @pytest.fixture
    def init_models(self, User, BlogPost, Address, Comment):
        pass

    def test_updates_foreign_keys(self, session, User, BlogPost, Address):
        john = User(name=u'John')
        jack = User(name=u'Jack')
        post = BlogPost(title=u'Some title', author=john)
        post2 = BlogPost(title=u'Other title', author=jack)
        address1 = Address(city=u'New York', user=john)
        address2 = Address(city=u'Los Angeles', user=jack)
        session.add(john)
        session.add(jack)
        session.add(post)
        session.add(post2)
        session.add(address1)
        session.add(address2)
        session.commit()
        merge_references(john, jack)
        session.commit()
        assert post.author == jack
        assert post2.author == jack
        assert address1.user == jack
        assert address2.user == jack

    def test_with_bad_foreign_keys(self, session, User, Comment):
        john = User(name=u'John')
        jack = User(name=u'Jack')
        with pytest.raises(ValueError):
            merge_references(
                john, jack, foreign_keys=Comment.__table__.foreign_keys)

    def test_with_foreign_keys(self, session, User, BlogPost, Address):
        john = User(name=u'John')
        jack = User(name=u'Jack')
        post = BlogPost(title=u'Some title', author=john)
        post2 = BlogPost(title=u'Other title', author=jack)
        address1 = Address(city=u'New York', user=john)
        address2 = Address(city=u'Los Angeles', user=jack)
        session.add(john)
        session.add(jack)
        session.add(post)
        session.add(post2)
        session.add(address1)
        session.add(address2)
        session.commit()
        merge_references(
            john, jack, foreign_keys=BlogPost.__table__.foreign_keys)
        assert post.author_id == jack.id
        assert post2.author_id == jack.id
        assert address1.user_id == john.id
        assert address2.user_id == jack.id

    def test_object_merging_whenever_possible(self, session, User, BlogPost):
        john = User(name=u'John')
        jack = User(name=u'Jack')
        post = BlogPost(title=u'Some title', author=john)
        post2 = BlogPost(title=u'Other title', author=jack)
        session.add(john)
        session.add(jack)
        session.add(post)
        session.add(post2)
        session.commit()
        # Load the author for post
        assert post.author_id == john.id
        merge_references(john, jack)
        assert post.author_id == jack.id
        assert post2.author_id == jack.id


class TestMergeReferencesWithManyToManyAssociations(object):

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            def __repr__(self):
                return 'User(%r)' % self.name
        return User

    @pytest.fixture
    def Team(self, Base):
        team_member = sa.Table(
            'team_member', Base.metadata,
            sa.Column(
                'user_id', sa.Integer,
                sa.ForeignKey('user.id', ondelete='CASCADE'),
                primary_key=True
            ),
            sa.Column(
                'team_id', sa.Integer,
                sa.ForeignKey('team.id', ondelete='CASCADE'),
                primary_key=True
            )
        )

        class Team(Base):
            __tablename__ = 'team'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            members = sa.orm.relationship(
                'User',
                secondary=team_member,
                backref='teams'
            )
        return Team

    @pytest.fixture
    def init_models(self, User, Team):
        pass

    def test_supports_associations(self, session, User, Team):
        john = User(name=u'John')
        jack = User(name=u'Jack')
        team = Team(name=u'Team')
        team.members.append(john)
        session.add(john)
        session.add(jack)
        session.commit()
        merge_references(john, jack)
        assert john not in team.members
        assert jack in team.members


class TestMergeReferencesWithManyToManyAssociationObjects(object):

    @pytest.fixture
    def Team(self, Base):
        class Team(Base):
            __tablename__ = 'team'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return Team

    @pytest.fixture
    def User(self, Base):
        class User(Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))
        return User

    @pytest.fixture
    def TeamMember(self, Base, User, Team):
        class TeamMember(Base):
            __tablename__ = 'team_member'
            user_id = sa.Column(
                sa.Integer,
                sa.ForeignKey(User.id, ondelete='CASCADE'),
                primary_key=True
            )
            team_id = sa.Column(
                sa.Integer,
                sa.ForeignKey(Team.id, ondelete='CASCADE'),
                primary_key=True
            )
            role = sa.Column(sa.Unicode(255))
            team = sa.orm.relationship(
                Team,
                backref=sa.orm.backref(
                    'members',
                    cascade='all, delete-orphan'
                ),
                primaryjoin=team_id == Team.id,
            )
            user = sa.orm.relationship(
                User,
                backref=sa.orm.backref(
                    'memberships',
                    cascade='all, delete-orphan'
                ),
                primaryjoin=user_id == User.id,
            )
        return TeamMember

    @pytest.fixture
    def init_models(self, User, Team, TeamMember):
        pass

    def test_supports_associations(self, session, User, Team, TeamMember):
        john = User(name=u'John')
        jack = User(name=u'Jack')
        team = Team(name=u'Team')
        team.members.append(TeamMember(user=john))
        session.add(john)
        session.add(jack)
        session.add(team)
        session.commit()
        merge_references(john, jack)
        session.commit()
        users = [member.user for member in team.members]
        assert john not in users
        assert jack in users
