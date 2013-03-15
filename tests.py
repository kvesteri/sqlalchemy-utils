import sqlalchemy as sa

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import escape_like, sort_query, InstrumentedList


engine = create_engine(
    'sqlite:///'
)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()


class Category(Base):
    __tablename__ = 'category'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(255))


class Article(Base):
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


class TestInstrumentedList(object):
    def test_any_returns_true_if_member_has_attr_defined(self):
        category = Category()
        category.articles.append(Article())
        category.articles.append(Article(name=u'some name'))
        assert category.articles.any('name')

    def test_any_returns_false_if_no_member_has_attr_defined(self):
        category = Category()
        category.articles.append(Article())
        assert not category.articles.any('name')


class TestEscapeLike(object):
    def test_escapes_wildcards(self):
        assert escape_like('_*%') == '*_***%'


class TestSortQuery(object):
    def test_without_sort_param_returns_the_query_object_untouched(self):
        query = session.query(Article)
        sorted_query = sort_query(query, '')
        assert query == sorted_query

    def test_sort_by_column_ascending(self):
        query = sort_query(session.query(Article), 'name')
        assert 'ORDER BY article.name ASC' in str(query)

    def test_sort_by_column_descending(self):
        query = sort_query(session.query(Article), '-name')
        assert 'ORDER BY article.name DESC' in str(query)

    def test_skips_unknown_columns(self):
        query = session.query(Article)
        sorted_query = sort_query(query, '-unknown')
        assert query == sorted_query

    def test_sort_by_calculated_value_ascending(self):
        query = session.query(
            Category, sa.func.count(Article.id).label('articles')
        )
        query = sort_query(query, 'articles')
        assert 'ORDER BY articles ASC' in str(query)

    def test_sort_by_calculated_value_descending(self):
        query = session.query(
            Category, sa.func.count(Article.id).label('articles')
        )
        query = sort_query(query, '-articles')
        assert 'ORDER BY articles DESC' in str(query)

    def test_sort_by_joined_table_column(self):
        query = session.query(Article).join(Article.category)
        sorted_query = sort_query(query, 'category-name')
        assert 'category.name ASC' in str(sorted_query)
