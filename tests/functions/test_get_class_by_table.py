import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_class_by_table


class TestGetClassByTableWithJoinedTableInheritance:

    @pytest.fixture
    def Entity(self, Base):
        class Entity(Base):
            __tablename__ = 'entity'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)
            type = sa.Column(sa.String)
            __mapper_args__ = {
                'polymorphic_on': type,
                'polymorphic_identity': 'entity'
            }
        return Entity

    @pytest.fixture
    def User(self, Entity):
        class User(Entity):
            __tablename__ = 'user'
            id = sa.Column(
                sa.Integer,
                sa.ForeignKey(Entity.id, ondelete='CASCADE'),
                primary_key=True
            )
            __mapper_args__ = {
                'polymorphic_identity': 'user'
            }
        return User

    def test_returns_class(self, Base, User, Entity):
        assert get_class_by_table(Base, User.__table__) == User
        assert get_class_by_table(
            Base,
            Entity.__table__
        ) == Entity

    def test_table_with_no_associated_class(self, Base):
        table = sa.Table(
            'some_table',
            Base.metadata,
            sa.Column('id', sa.Integer)
        )
        assert get_class_by_table(Base, table) is None


class TestGetClassByTableWithSingleTableInheritance:

    @pytest.fixture
    def Entity(self, Base):
        class Entity(Base):
            __tablename__ = 'entity'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)
            type = sa.Column(sa.String)
            __mapper_args__ = {
                'polymorphic_on': type,
                'polymorphic_identity': 'entity'
            }
        return Entity

    @pytest.fixture
    def User(self, Entity):
        class User(Entity):
            __mapper_args__ = {
                'polymorphic_identity': 'user'
            }
        return User

    def test_multiple_classes_without_data_parameter(self, Base, Entity, User):
        with pytest.raises(ValueError):
            assert get_class_by_table(
                Base,
                Entity.__table__
            )

    def test_multiple_classes_with_data_parameter(self, Base, Entity, User):
        assert get_class_by_table(
            Base,
            Entity.__table__,
            {'type': 'entity'}
        ) == Entity
        assert get_class_by_table(
            Base,
            Entity.__table__,
            {'type': 'user'}
        ) == User

    def test_multiple_classes_with_bogus_data(self, Base, Entity, User):
        with pytest.raises(ValueError):
            assert get_class_by_table(
                Base,
                Entity.__table__,
                {'type': 'unknown'}
            )
