import pytest
import sqlalchemy as sa

from sqlalchemy_utils.aggregates import aggregated


@pytest.fixture
def Thread(Base):
    class Thread(Base):
        __tablename__ = 'thread'
        id = sa.Column(sa.Integer, primary_key=True)

        @aggregated(
            'comments',
            sa.Column('_comment_count', sa.Integer, default=0)
        )
        def comment_count(self):
            return sa.func.count('1')

        comments = sa.orm.relationship('Comment', backref='thread')
    return Thread


@pytest.fixture
def Comment(Base):
    class Comment(Base):
        __tablename__ = 'comment'
        id = sa.Column(sa.Integer, primary_key=True)
        thread_id = sa.Column(sa.Integer, sa.ForeignKey('thread.id'))
    return Comment


@pytest.fixture
def init_models(Thread, Comment):
    pass


class TestAggregatedWithColumnAlias:

    def test_assigns_aggregates_on_insert(self, session, Thread, Comment):
        thread = Thread()
        session.add(thread)
        comment = Comment(thread=thread)
        session.add(comment)
        session.commit()
        session.refresh(thread)
        assert thread.comment_count == 1

    def test_assigns_aggregates_on_separate_insert(
        self,
        session,
        Thread,
        Comment
    ):
        thread = Thread()
        session.add(thread)
        session.commit()
        comment = Comment(thread=thread)
        session.add(comment)
        session.commit()
        session.refresh(thread)
        assert thread.comment_count == 1

    def test_assigns_aggregates_on_delete(self, session, Thread, Comment):
        thread = Thread()
        session.add(thread)
        session.commit()
        comment = Comment(thread=thread)
        session.add(comment)
        session.commit()
        session.delete(comment)
        session.commit()
        session.refresh(thread)
        assert thread.comment_count == 0
