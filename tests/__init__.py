import sqlalchemy as sa

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import (
    InstrumentedList,
    PhoneNumberType,
)


@sa.event.listens_for(sa.engine.Engine, 'before_cursor_execute')
def count_sql_calls(conn, cursor, statement, parameters, context, executemany):
    try:
        conn.query_count += 1
    except AttributeError:
        conn.query_count = 0


class TestCase(object):
    def setup_method(self, method):
        self.engine = create_engine('sqlite:///:memory:')
        self.connection = self.engine.connect()
        self.Base = declarative_base()
        self.Base2 = declarative_base()
        self.create_models()
        self.Base.metadata.create_all(self.connection)

        Session = sessionmaker(bind=self.connection)
        self.session = Session()

    def teardown_method(self, method):
        self.session.close_all()
        self.Base.metadata.drop_all(self.connection)
        self.connection.close()
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
