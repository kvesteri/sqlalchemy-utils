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
    return Thread


@pytest.fixture
def Comment(Base, Thread):
    class Comment(Base):
        __tablename__ = 'comment'
        id = sa.Column(sa.Integer, primary_key=True)
        content = sa.Column(sa.Unicode(255))
        thread_id = sa.Column(sa.Integer, sa.ForeignKey('thread.id'))

        thread = sa.orm.relationship(Thread, backref='comments')
    return Comment


@pytest.fixture
def init_models(Thread, Comment):
    pass


class TestAggregateValueGenerationWithBackrefs:

    def test_assigns_aggregates_on_insert(self, session, Thread, Comment):
        thread = Thread()
        thread.name = 'some article name'
        session.add(thread)
        comment = Comment(content='Some content', thread=thread)
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
        thread.name = 'some article name'
        session.add(thread)
        session.commit()
        comment = Comment(content='Some content', thread=thread)
        session.add(comment)
        session.commit()
        session.refresh(thread)
        assert thread.comment_count == 1

    def test_assigns_aggregates_on_delete(self, session, Thread, Comment):
        thread = Thread()
        thread.name = 'some article name'
        session.add(thread)
        session.commit()
        comment = Comment(content='Some content', thread=thread)
        session.add(comment)
        session.commit()
        session.delete(comment)
        session.commit()
        session.refresh(thread)
        assert thread.comment_count == 0
