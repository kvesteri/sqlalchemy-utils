import pytest
import sqlalchemy as sa

from sqlalchemy_utils import Ltree, LtreeType


@pytest.fixture
def Section(Base):
    class Section(Base):
        __tablename__ = 'section'
        id = sa.Column(sa.Integer, primary_key=True)
        path = sa.Column(LtreeType)

    return Section


@pytest.fixture
def init_models(Section, connection):
    connection.execute('CREATE EXTENSION IF NOT EXISTS ltree')
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestLTREE(object):
    def test_saves_path(self, session, Section):
        section = Section(path='1.1.2')

        session.add(section)
        session.commit()

        user = session.query(Section).first()
        assert user.path == '1.1.2'

    def test_scalar_attributes_get_coerced_to_objects(self, Section):
        section = Section(path='path.path')
        assert isinstance(section.path, Ltree)

    def test_literal_param(self, session, Section):
        clause = Section.path == 'path'
        compiled = str(clause.compile(compile_kwargs={'literal_binds': True}))
        assert compiled == 'section.path = \'path\''
