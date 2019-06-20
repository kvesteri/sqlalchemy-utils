import pytest
import sqlalchemy as sa

from sqlalchemy_utils import get_class_by_tablename


class TestGetTableByName(object):
    def test_does_have_table(self, Base):

        class User(Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)

        table = get_class_by_tablename(Base, 'user')

        assert table == User

    def test_does_not_have_table(self, Base):

        class User(Base):
            __tablename__ = 'user'
            first_name = sa.Column(sa.Unicode(255), primary_key=True)
            last_name = sa.Column(sa.Unicode(255), primary_key=True)

        
        with pytest.raises(ValueError):
            table = get_class_by_tablename(Base, 'not_user')
