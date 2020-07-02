import pytest
import sqlalchemy as sa
from sqlalchemy.orm import dynamic_loader

from sqlalchemy_utils.observer import observes


@pytest.fixture
def Director(Base):
    class Director(Base):
        __tablename__ = 'director'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        movies = dynamic_loader('Movie', back_populates='director')

    return Director


@pytest.fixture
def Movie(Base, Director):
    class Movie(Base):
        __tablename__ = 'movie'
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String)
        director_id = sa.Column(sa.Integer, sa.ForeignKey(Director.id))
        director = sa.orm.relationship(Director, back_populates='movies')
        director_name = sa.Column(sa.String)

        @observes('director')
        def director_observer(self, director):
            self.director_name = director.name

    return Movie


@pytest.fixture
def init_models(Director, Movie):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestObservesForDynamicRelationship:
    def test_add_observed_object(self, session, Director, Movie):
        steven = Director(name='Steven Spielberg')
        session.add(steven)
        jaws = Movie(name='Jaws', director=steven)
        session.add(jaws)
        session.commit()
        assert jaws.director_name == 'Steven Spielberg'

    def test_add_observed_object_from_backref(self, session, Director, Movie):
        jaws = Movie(name='Jaws')
        steven = Director(name='Steven Spielberg', movies=[jaws])
        session.add(steven)
        session.add(jaws)
        session.commit()
        assert jaws.director_name == 'Steven Spielberg'
