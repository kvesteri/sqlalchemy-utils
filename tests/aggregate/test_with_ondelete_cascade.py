import pytest
import sqlalchemy as sa

from sqlalchemy_utils.aggregates import aggregated


@pytest.fixture
def Thread(Base):
    class Thread(Base):
        __tablename__ = 'thread'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated('comments', sa.Column(sa.Integer, default=0))
        def comment_count(self):
            return sa.func.count('1')

        comments = sa.orm.relationship(
            'Comment',
            passive_deletes=True,
            backref='thread'
        )
    return Thread


@pytest.fixture
def Comment(Base):
    class Comment(Base):
        __tablename__ = 'comment'
        id = sa.Column(sa.Integer, primary_key=True)
        content = sa.Column(sa.Unicode(255))
        thread_id = sa.Column(
            sa.Integer,
            sa.ForeignKey('thread.id', ondelete='CASCADE')
        )
    return Comment


@pytest.fixture
def init_models(Thread, Comment):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestAggregateValueGenerationWithCascadeDelete:

    def test_something(self, session, Thread, Comment):
        thread = Thread()
        thread.name = 'some article name'
        session.add(thread)
        comment = Comment(content='Some content', thread=thread)
        session.add(comment)
        session.commit()
        session.expire_all()
        session.delete(thread)
        session.commit()
