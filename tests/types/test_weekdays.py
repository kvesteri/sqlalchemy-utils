from babel import Locale
import sqlalchemy as sa
from sqlalchemy_utils.types import WeekDaysType
from sqlalchemy_utils.primitives import WeekDays
from sqlalchemy_utils import i18n

from tests import TestCase


class WeekDaysTypeTestCase(TestCase):
    def setup_method(self, method):
        TestCase.setup_method(self, method)
        i18n.get_locale = lambda: Locale('en')

    def create_models(self):
        class Schedule(self.Base):
            __tablename__ = 'schedule'
            id = sa.Column(sa.Integer, primary_key=True)
            working_days = sa.Column(WeekDaysType)

            def __repr__(self):
                return 'Schedule(%r)' % self.id

        self.Schedule = Schedule

    def test_color_parameter_processing(self):
        schedule = self.Schedule(
            working_days='0001111'
        )
        self.session.add(schedule)
        self.session.commit()

        schedule = self.session.query(self.Schedule).first()
        assert isinstance(schedule.working_days, WeekDays)

    def test_scalar_attributes_get_coerced_to_objects(self):
        schedule = self.Schedule(working_days=u'1010101')

        assert isinstance(schedule.working_days, WeekDays)


class TestWeekDaysTypeOnSQLite(WeekDaysTypeTestCase):
    dns = 'sqlite:///:memory:'


class TestWeekDaysTypeOnPostgres(WeekDaysTypeTestCase):
    dns = 'postgres://postgres@localhost/sqlalchemy_utils_test'


class TestWeekDaysTypeOnMySQL(WeekDaysTypeTestCase):
    dns = 'mysql+pymysql://travis@localhost/sqlalchemy_utils_test'
