import pytest
import sqlalchemy as sa

from sqlalchemy_utils import i18n
from sqlalchemy_utils.compat import _select_args
from sqlalchemy_utils.primitives import WeekDays
from sqlalchemy_utils.types import WeekDaysType


@pytest.fixture
def Schedule(Base):
    class Schedule(Base):
        __tablename__ = 'schedule'
        id = sa.Column(sa.Integer, primary_key=True)
        working_days = sa.Column(WeekDaysType)

        def __repr__(self):
            return 'Schedule(%r)' % self.id
    return Schedule


@pytest.fixture
def init_models(Schedule):
    pass


@pytest.fixture
def set_get_locale():
    i18n.get_locale = lambda: i18n.babel.Locale('en')


@pytest.mark.usefixtures('set_get_locale')
@pytest.mark.skipif('i18n.babel is None')
class WeekDaysTypeTestCase:
    def test_color_parameter_processing(self, session, Schedule):
        schedule = Schedule(
            working_days=b'0001111'
        )
        session.add(schedule)
        session.commit()

        schedule = session.query(Schedule).first()
        assert isinstance(schedule.working_days, WeekDays)

    def test_scalar_attributes_get_coerced_to_objects(self, Schedule):
        schedule = Schedule(working_days=b'1010101')

        assert isinstance(schedule.working_days, WeekDays)

    def test_compilation(self, Schedule, session):
        query = sa.select(*_select_args(Schedule.working_days))
        # the type should be cacheable and not throw exception
        session.execute(query)


@pytest.mark.usefixtures('sqlite_memory_dsn')
class TestWeekDaysTypeOnSQLite(WeekDaysTypeTestCase):
    pass


@pytest.mark.usefixtures('postgresql_dsn')
class TestWeekDaysTypeOnPostgres(WeekDaysTypeTestCase):
    pass


@pytest.mark.usefixtures('mysql_dsn')
class TestWeekDaysTypeOnMySQL(WeekDaysTypeTestCase):
    pass
