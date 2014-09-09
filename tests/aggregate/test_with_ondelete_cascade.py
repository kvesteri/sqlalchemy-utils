import sqlalchemy as sa
from sqlalchemy_utils.aggregates import aggregated
from tests import TestCase


class TestAggregateValueGenerationWithCascadeDelete(TestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'

    def create_models(self):
        class Thread(self.Base):
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

        class Comment(self.Base):
            __tablename__ = 'comment'
            id = sa.Column(sa.Integer, primary_key=True)
            content = sa.Column(sa.Unicode(255))
            thread_id = sa.Column(
                sa.Integer,
                sa.ForeignKey('thread.id', ondelete='CASCADE')
            )

        self.Thread = Thread
        self.Comment = Comment

    def test_something(self):
        thread = self.Thread()
        thread.name = u'some article name'
        self.session.add(thread)
        comment = self.Comment(content=u'Some content', thread=thread)
        self.session.add(comment)
        self.session.commit()
        self.session.expire_all()
        self.session.delete(thread)
        self.session.commit()
