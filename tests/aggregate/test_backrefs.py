import sqlalchemy as sa
from sqlalchemy_utils.aggregates import aggregated
from tests import TestCase


class TestAggregateValueGenerationWithBackrefs(TestCase):
    def create_models(self):
        class Thread(self.Base):
            __tablename__ = 'thread'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            @aggregated('comments', sa.Column(sa.Integer, default=0))
            def comment_count(self):
                return sa.func.count('1')

        class Comment(self.Base):
            __tablename__ = 'comment'
            id = sa.Column(sa.Integer, primary_key=True)
            content = sa.Column(sa.Unicode(255))
            thread_id = sa.Column(sa.Integer, sa.ForeignKey('thread.id'))

            thread = sa.orm.relationship(Thread, backref='comments')

        self.Thread = Thread
        self.Comment = Comment

    def test_assigns_aggregates_on_insert(self):
        thread = self.Thread()
        thread.name = u'some article name'
        self.session.add(thread)
        comment = self.Comment(content=u'Some content', thread=thread)
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(thread)
        assert thread.comment_count == 1

    def test_assigns_aggregates_on_separate_insert(self):
        thread = self.Thread()
        thread.name = u'some article name'
        self.session.add(thread)
        self.session.commit()
        comment = self.Comment(content=u'Some content', thread=thread)
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(thread)
        assert thread.comment_count == 1

    def test_assigns_aggregates_on_delete(self):
        thread = self.Thread()
        thread.name = u'some article name'
        self.session.add(thread)
        self.session.commit()
        comment = self.Comment(content=u'Some content', thread=thread)
        self.session.add(comment)
        self.session.commit()
        self.session.delete(comment)
        self.session.commit()
        self.session.refresh(thread)
        assert thread.comment_count == 0
