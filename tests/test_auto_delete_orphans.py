import pytest
import sqlalchemy as sa
from sqlalchemy.orm import backref

from sqlalchemy_utils import auto_delete_orphans, ImproperlyConfigured


@pytest.fixture
def tagging_tbl(Base):
    return sa.Table(
        'tagging',
        Base.metadata,
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


@pytest.fixture
def Tag(Base):
    class Tag(Base):
        __tablename__ = 'tag'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(100), unique=True, nullable=False)

        def __init__(self, name=None):
            self.name = name
    return Tag


@pytest.fixture(
    params=['entries', backref('entries', lazy='select')],
    ids=['backref_string', 'backref_with_keywords']
)
def Entry(Base, Tag, tagging_tbl, request):
    class Entry(Base):
        __tablename__ = 'entry'

        id = sa.Column(sa.Integer, primary_key=True)

        tags = sa.orm.relationship(
            Tag,
            secondary=tagging_tbl,
            backref=request.param
        )
    auto_delete_orphans(Entry.tags)
    return Entry


@pytest.fixture
def EntryWithoutTagsBackref(Base, Tag, tagging_tbl):
    class EntryWithoutTagsBackref(Base):
        __tablename__ = 'entry'

        id = sa.Column(sa.Integer, primary_key=True)

        tags = sa.orm.relationship(
            Tag,
            secondary=tagging_tbl
        )
    return EntryWithoutTagsBackref


class TestAutoDeleteOrphans:

    @pytest.fixture
    def init_models(self, Entry, Tag):
        pass

    def test_orphan_deletion(self, session, Entry, Tag):
        r1 = Entry()
        r2 = Entry()
        r3 = Entry()
        t1, t2, t3, t4 = (
            Tag('t1'),
            Tag('t2'),
            Tag('t3'),
            Tag('t4')
        )

        r1.tags.extend([t1, t2])
        r2.tags.extend([t2, t3])
        r3.tags.extend([t4])
        session.add_all([r1, r2, r3])

        assert session.query(Tag).count() == 4
        r2.tags.remove(t2)
        assert session.query(Tag).count() == 4
        r1.tags.remove(t2)
        assert session.query(Tag).count() == 3
        r1.tags.remove(t1)
        assert session.query(Tag).count() == 2


class TestAutoDeleteOrphansWithoutBackref:

    @pytest.fixture
    def init_models(self, EntryWithoutTagsBackref, Tag):
        pass

    def test_orphan_deletion(self, EntryWithoutTagsBackref):
        with pytest.raises(ImproperlyConfigured):
            auto_delete_orphans(EntryWithoutTagsBackref.tags)
