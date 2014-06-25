from pytest import raises
import sqlalchemy as sa
from sqlalchemy_utils import auto_delete_orphans, ImproperlyConfigured

from tests import TestCase


class TestAutoDeleteOrphans(TestCase):
    def create_models(self):
        tagging = sa.Table(
            'tagging',
            self.Base.metadata,
            sa.Column(
                'tag_id',
                sa.Integer,
                sa.ForeignKey('tag.id', ondelete='cascade'),
                primary_key=True
            ),
            sa.Column(
                'entry_id',
                sa.Integer,
                sa.ForeignKey('entry.id', ondelete='cascade'),
                primary_key=True
            )
        )

        class Tag(self.Base):
            __tablename__ = 'tag'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(100), unique=True, nullable=False)

            def __init__(self, name=None):
                self.name = name

        class Entry(self.Base):
            __tablename__ = 'entry'

            id = sa.Column(sa.Integer, primary_key=True)

            tags = sa.orm.relationship(
                'Tag',
                secondary=tagging,
                backref='entries'
            )

        auto_delete_orphans(Entry.tags)

        self.Tag = Tag
        self.Entry = Entry

    def test_orphan_deletion(self):
        r1 = self.Entry()
        r2 = self.Entry()
        r3 = self.Entry()
        t1, t2, t3, t4 = (
            self.Tag('t1'),
            self.Tag('t2'),
            self.Tag('t3'),
            self.Tag('t4')
        )

        r1.tags.extend([t1, t2])
        r2.tags.extend([t2, t3])
        r3.tags.extend([t4])
        self.session.add_all([r1, r2, r3])

        assert self.session.query(self.Tag).count() == 4
        r2.tags.remove(t2)
        assert self.session.query(self.Tag).count() == 4
        r1.tags.remove(t2)
        assert self.session.query(self.Tag).count() == 3
        r1.tags.remove(t1)
        assert self.session.query(self.Tag).count() == 2


class TestAutoDeleteOrphansWithoutBackref(TestCase):
    def create_models(self):
        tagging = sa.Table(
            'tagging',
            self.Base.metadata,
            sa.Column(
                'tag_id',
                sa.Integer,
                sa.ForeignKey('tag.id', ondelete='cascade'),
                primary_key=True
            ),
            sa.Column(
                'entry_id',
                sa.Integer,
                sa.ForeignKey('entry.id', ondelete='cascade'),
                primary_key=True
            )
        )

        class Tag(self.Base):
            __tablename__ = 'tag'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String(100), unique=True, nullable=False)

            def __init__(self, name=None):
                self.name = name

        class Entry(self.Base):
            __tablename__ = 'entry'

            id = sa.Column(sa.Integer, primary_key=True)

            tags = sa.orm.relationship(
                'Tag',
                secondary=tagging
            )

        self.Entry = Entry

    def test_orphan_deletion(self):
        with raises(ImproperlyConfigured):
            auto_delete_orphans(self.Entry.tags)
