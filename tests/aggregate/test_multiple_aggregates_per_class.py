import pytest
import sqlalchemy as sa

from sqlalchemy_utils.aggregates import aggregated


@pytest.fixture
def Comment(Base):
    class Comment(Base):
        __tablename__ = 'comment'
        id = sa.Column(sa.Integer, primary_key=True)
        content = sa.Column(sa.Unicode(255))
        thread_id = sa.Column(sa.Integer, sa.ForeignKey('thread.id'))
    return Comment


@pytest.fixture
def Thread(Base, Comment):
    class Thread(Base):
        __tablename__ = 'thread'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))

        @aggregated(
            'comments',
            sa.Column(sa.Integer, default=0)
        )
        def comment_count(self):
            return sa.func.count('1')

        @aggregated('comments', sa.Column(sa.Integer))
        def last_comment_id(self):
            return sa.func.max(Comment.id)

        comments = sa.orm.relationship(
            'Comment',
            backref='thread'
        )

    Thread.last_comment = sa.orm.relationship(
        'Comment',
        primaryjoin='Thread.last_comment_id == Comment.id',
        foreign_keys=[Thread.last_comment_id],
        viewonly=True
    )
    return Thread


@pytest.fixture
def init_models(Comment, Thread):
    pass


class TestAggregateValueGenerationForSimpleModelPaths:

    def test_assigns_aggregates_on_insert(self, session, Thread, Comment):
        thread = Thread()
        thread.name = 'some article name'
        session.add(thread)
        comment = Comment(content='Some content', thread=thread)
        session.add(comment)
        session.commit()
        session.refresh(thread)
        assert thread.comment_count == 1
        assert thread.last_comment_id == comment.id

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
        assert thread.last_comment_id == 1

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
        assert thread.last_comment_id is None
