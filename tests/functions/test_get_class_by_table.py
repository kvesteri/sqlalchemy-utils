import sqlalchemy as sa
from pytest import raises
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_utils import get_class_by_table


class TestGetClassByTableWithJoinedTableInheritance(object):
    def setup_method(self, method):
        self.Base = declarative_base()

        class Entity(self.Base):
            __tablename__ = 'entity'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)
            type = sa.Column(sa.String)
            __mapper_args__ = {
                'polymorphic_on': type,
                'polymorphic_identity': 'entity'
            }

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

        self.Entity = Entity
        self.User = User

    def test_returns_class(self):
        assert get_class_by_table(self.Base, self.User.__table__) == self.User
        assert get_class_by_table(
            self.Base,
            self.Entity.__table__
        ) == self.Entity

    def test_table_with_no_associated_class(self):
        table = sa.Table(
            'some_table',
            self.Base.metadata,
            sa.Column('id', sa.Integer)
        )
        assert get_class_by_table(self.Base, table) is None


class TestGetClassByTableWithSingleTableInheritance(object):
    def setup_method(self, method):
        self.Base = declarative_base()

        class Entity(self.Base):
            __tablename__ = 'entity'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.String)
            type = sa.Column(sa.String)
            __mapper_args__ = {
                'polymorphic_on': type,
                'polymorphic_identity': 'entity'
            }

        class User(Entity):
            __mapper_args__ = {
                'polymorphic_identity': 'user'
            }

        self.Entity = Entity
        self.User = User

    def test_multiple_classes_without_data_parameter(self):
        with raises(ValueError):
            assert get_class_by_table(
                self.Base,
                self.Entity.__table__
            )

    def test_multiple_classes_with_data_parameter(self):
        assert get_class_by_table(
            self.Base,
            self.Entity.__table__,
            {'type': 'entity'}
        ) == self.Entity
        assert get_class_by_table(
            self.Base,
            self.Entity.__table__,
            {'type': 'user'}
        ) == self.User

    def test_multiple_classes_with_bogus_data(self):
        with raises(ValueError):
            assert get_class_by_table(
                self.Base,
                self.Entity.__table__,
                {'type': 'unknown'}
            )
