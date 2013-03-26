import sqlalchemy as sa

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import (
    escape_like,
    sort_query,
    InstrumentedList,
    PhoneNumber,
    PhoneNumberType,
    merge
)


class TestCase(object):

    def setup_method(self, method):
        self.engine = create_engine('sqlite:///:memory:')
        self.Base = declarative_base()

        self.create_models()
        self.Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def teardown_method(self, method):
        self.session.close_all()
        self.Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            phone_number = sa.Column(PhoneNumberType())

        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Article(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            category_id = sa.Column(sa.Integer, sa.ForeignKey(Category.id))

            category = sa.orm.relationship(
                Category,
                primaryjoin=category_id == Category.id,
                backref=sa.orm.backref(
                    'articles',
                    collection_class=InstrumentedList
                )
            )

        self.User = User
        self.Category = Category
        self.Article = Article


class TestInstrumentedList(TestCase):
    def test_any_returns_true_if_member_has_attr_defined(self):
        category = self.Category()
        category.articles.append(self.Article())
        category.articles.append(self.Article(name=u'some name'))
        assert category.articles.any('name')

    def test_any_returns_false_if_no_member_has_attr_defined(self):
        category = self.Category()
        category.articles.append(self.Article())
        assert not category.articles.any('name')


class TestEscapeLike(TestCase):
    def test_escapes_wildcards(self):
        assert escape_like('_*%') == '*_***%'


class TestSortQuery(TestCase):
    def test_without_sort_param_returns_the_query_object_untouched(self):
        query = self.session.query(self.Article)
        sorted_query = sort_query(query, '')
        assert query == sorted_query

    def test_sort_by_column_ascending(self):
        query = sort_query(self.session.query(self.Article), 'name')
        assert 'ORDER BY article.name ASC' in str(query)

    def test_sort_by_column_descending(self):
        query = sort_query(self.session.query(self.Article), '-name')
        assert 'ORDER BY article.name DESC' in str(query)

    def test_skips_unknown_columns(self):
        query = self.session.query(self.Article)
        sorted_query = sort_query(query, '-unknown')
        assert query == sorted_query

    def test_sort_by_calculated_value_ascending(self):
        query = self.session.query(
            self.Category, sa.func.count(self.Article.id).label('articles')
        )
        query = sort_query(query, 'articles')
        assert 'ORDER BY articles ASC' in str(query)

    def test_sort_by_calculated_value_descending(self):
        query = self.session.query(
            self.Category, sa.func.count(self.Article.id).label('articles')
        )
        query = sort_query(query, '-articles')
        assert 'ORDER BY articles DESC' in str(query)

    def test_sort_by_joined_table_column(self):
        query = self.session.query(self.Article).join(self.Article.category)
        sorted_query = sort_query(query, 'category-name')
        assert 'category.name ASC' in str(sorted_query)


class TestPhoneNumber(object):
    def setup_method(self, method):
        self.valid_phone_numbers = [
            '040 1234567',
            '+358 401234567',
            '09 2501234',
            '+358 92501234',
            '0800 939393',
            '09 4243 0456',
            '0600 900 500'
        ]
        self.invalid_phone_numbers = [
            'abc',
            '+040 1234567',
            '0111234567',
            '358'
        ]

    def test_valid_phone_numbers(self):
        for raw_number in self.valid_phone_numbers:
            phone_number = PhoneNumber(raw_number, 'FI')
            assert phone_number.is_valid_number()

    def test_invalid_phone_numbers(self):
        for raw_number in self.invalid_phone_numbers:
            try:
                phone_number = PhoneNumber(raw_number, 'FI')
                assert not phone_number.is_valid_number()
            except:
                pass

    def test_phone_number_attributes(self):
        phone_number = PhoneNumber('+358401234567')
        assert phone_number.e164 == u'+358401234567'
        assert phone_number.international == u'+358 40 1234567'
        assert phone_number.national == u'040 1234567'


class TestPhoneNumberType(TestCase):
    def setup_method(self, method):
        super(TestPhoneNumberType, self).setup_method(method)
        self.phone_number = PhoneNumber(
            '040 1234567',
            'FI'
        )
        self.user = self.User()
        self.user.name = u'Someone'
        self.user.phone_number = self.phone_number
        self.session.add(self.user)
        self.session.commit()

    def test_query_returns_phone_number_object(self):
        queried_user = self.session.query(self.User).first()
        assert queried_user.phone_number == self.phone_number

    def test_phone_number_is_stored_as_string(self):
        result = self.session.execute(
            'SELECT phone_number FROM user WHERE id=:param',
            {'param': self.user.id}
        )
        assert result.first()[0] == u'+358401234567'


class DatabaseTestCase(object):
    def create_models(self):
        pass

    def setup_method(self, method):
        self.engine = create_engine(
            'sqlite:///'
        )
        #self.engine.echo = True
        self.Base = declarative_base()

        self.create_models()
        self.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def teardown_method(self, method):
        self.engine.dispose()
        self.Base.metadata.drop_all(self.engine)
        self.session.expunge_all()


class TestMerge(DatabaseTestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            def __repr__(self):
                return 'User(%r)' % self.name

        class BlogPost(self.Base):
            __tablename__ = 'blog_post'
            id = sa.Column(sa.Integer, primary_key=True)
            title = sa.Column(sa.Unicode(255))
            content = sa.Column(sa.UnicodeText)
            author_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))

            author = sa.orm.relationship(User)

        self.User = User
        self.BlogPost = BlogPost

    def test_updates_foreign_keys(self):
        john = self.User(name=u'John')
        jack = self.User(name=u'Jack')
        post = self.BlogPost(title=u'Some title', author=john)
        post2 = self.BlogPost(title=u'Other title', author=jack)
        self.session.add(john)
        self.session.add(jack)
        self.session.add(post)
        self.session.add(post2)
        self.session.commit()
        merge(john, jack)
        assert post.author == jack
        assert post2.author == jack

    def test_deletes_from_entity(self):
        john = self.User(name=u'John')
        jack = self.User(name=u'Jack')
        self.session.add(john)
        self.session.add(jack)
        self.session.commit()
        merge(john, jack)
        assert john in self.session.deleted


class TestMergeManyToManyAssociations(DatabaseTestCase):
    def create_models(self):
        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            def __repr__(self):
                return 'User(%r)' % self.name

        team_member = sa.Table(
            'team_member', self.Base.metadata,
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

        class Team(self.Base):
            __tablename__ = 'team'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            members = sa.orm.relationship(
                User,
                secondary=team_member,
                backref='teams'
            )

        self.User = User
        self.Team = Team

    def test_when_association_only_exists_in_from_entity(self):
        john = self.User(name=u'John')
        jack = self.User(name=u'Jack')
        team = self.Team(name=u'Team')
        team.members.append(john)
        self.session.add(john)
        self.session.add(jack)
        self.session.commit()
        merge(john, jack)
        assert john not in team.members
        assert jack in team.members

    def test_when_association_exists_in_both(self):
        john = self.User(name=u'John')
        jack = self.User(name=u'Jack')
        team = self.Team(name=u'Team')
        team.members.append(john)
        team.members.append(jack)
        self.session.add(john)
        self.session.add(jack)
        self.session.commit()
        merge(john, jack)
        assert john not in team.members
        assert jack in team.members
        count = self.session.execute(
            'SELECT COUNT(1) FROM team_member'
        ).fetchone()[0]
        assert count == 1


class TestMergeManyToManyAssociationObjects(DatabaseTestCase):
    def create_models(self):
        class Team(self.Base):
            __tablename__ = 'team'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class User(self.Base):
            __tablename__ = 'user'
            id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class TeamMember(self.Base):
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

        self.User = User
        self.TeamMember = TeamMember
        self.Team = Team

    def test_when_association_only_exists_in_from_entity(self):
        john = self.User(name=u'John')
        jack = self.User(name=u'Jack')
        team = self.Team(name=u'Team')
        team.members.append(self.TeamMember(user=john))
        self.session.add(john)
        self.session.add(jack)
        self.session.add(team)
        self.session.commit()
        merge(john, jack)
        self.session.commit()
        users = [member.user for member in team.members]
        assert john not in users
        assert jack in users

    def test_when_association_exists_in_both(self):
        john = self.User(name=u'John')
        jack = self.User(name=u'Jack')
        team = self.Team(name=u'Team')
        team.members.append(self.TeamMember(user=john))
        team.members.append(self.TeamMember(user=jack))
        self.session.add(john)
        self.session.add(jack)
        self.session.add(team)
        self.session.commit()
        merge(john, jack)
        users = [member.user for member in team.members]
        assert john not in users
        assert jack in users
        assert self.session.query(self.TeamMember).count() == 1
