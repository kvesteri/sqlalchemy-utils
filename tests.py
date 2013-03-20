import phonenumbers
import sqlalchemy as sa

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import (
    escape_like,
    sort_query,
    InstrumentedList,
    PhoneNumberType
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


class TestPhoneNumberType(TestCase):
    def setup_method(self, method):
        super(TestPhoneNumberType, self).setup_method(method)
        self.phone_number = phonenumbers.parse(
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
