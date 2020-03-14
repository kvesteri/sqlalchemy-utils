import pytest
import sqlalchemy as sa

from sqlalchemy_utils.functions.orm import get_mapper, get_polymorphic_mappers


@pytest.fixture
def TextItem(Base):
    class TextItem(Base):
        __tablename__ = 'text_item'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        type = sa.Column(sa.Unicode(255))

        __mapper_args__ = {
            'polymorphic_on': type,
            'with_polymorphic': '*'
        }
    return TextItem


@pytest.fixture
def Article(TextItem):
    class Article(TextItem):
        __tablename__ = 'article'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
        )
        __mapper_args__ = {
            'polymorphic_identity': __tablename__
        }
    return Article


@pytest.fixture
def Comment(TextItem):
    class Comment(TextItem):
        __tablename__ = 'comment'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(TextItem.id), primary_key=True
        )
        __mapper_args__ = {
            'polymorphic_identity': __tablename__
        }
    return Comment


@pytest.fixture
def TextItem1(Base):
    class TextItem1(Base):
        __tablename__ = 'text_item1'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Unicode(255))
        type = sa.Column(sa.Unicode(255))

        __mapper_args__ = {
            'polymorphic_on': type,
        }
    return TextItem1


@pytest.fixture
def Article1(TextItem1):
    class Article1(TextItem1):
        __tablename__ = 'article1'
        id = sa.Column(
            sa.Integer, sa.ForeignKey(TextItem1.id), primary_key=True
        )
        __mapper_args__ = {
            'polymorphic_identity': __tablename__
        }
    return Article1


@pytest.fixture
def init_models(TextItem, Article, Comment, TextItem1, Article1):
    pass


def test_with_polymorphic(TextItem, Article, Comment):
    assert list(get_polymorphic_mappers(get_mapper(TextItem))) == [
        Article.__mapper__,
        Comment.__mapper__,
    ]


def test_no_with_polymorphic(TextItem1, Article1):
    assert list(get_polymorphic_mappers(get_mapper(TextItem1))) == []
    assert list(get_polymorphic_mappers(get_mapper(Article1))) == [
        Article1.__mapper__,
    ]


def test_classes(TextItem, Article, Comment):
    assert list(
        get_polymorphic_mappers(get_mapper(TextItem), classes=Article)
    ) == [
        Article.__mapper__,
    ]
    assert list(
        get_polymorphic_mappers(get_mapper(TextItem), classes=Comment)
    ) == [
        Comment.__mapper__,
    ]
    assert list(
        get_polymorphic_mappers(get_mapper(TextItem), classes='*')
    ) == [
        Article.__mapper__,
        Comment.__mapper__,
    ]
