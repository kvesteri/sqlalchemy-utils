import pytest
from flexmock import flexmock

from sqlalchemy_utils import i18n
from sqlalchemy_utils.primitives import WeekDay, WeekDays


@pytest.fixture
def set_get_locale():
    i18n.get_locale = lambda: i18n.babel.Locale('fi')


@pytest.mark.skipif('i18n.babel is None')
@pytest.mark.usefixtures('set_get_locale')
class TestWeekDay:

    def test_constructor_with_valid_index(self):
        day = WeekDay(1)
        assert day.index == 1

    @pytest.mark.parametrize('index', [-1, 7])
    def test_constructor_with_invalid_index(self, index):
        with pytest.raises(ValueError):
            WeekDay(index)

    def test_equality_with_equal_week_day(self):
        day = WeekDay(1)
        day2 = WeekDay(1)
        assert day == day2

    def test_equality_with_unequal_week_day(self):
        day = WeekDay(1)
        day2 = WeekDay(2)
        assert day != day2

    def test_equality_with_unsupported_comparison(self):
        day = WeekDay(1)
        assert day != 'foobar'

    def test_hash_is_equal_to_index_hash(self):
        day = WeekDay(1)
        assert hash(day) == hash(day.index)

    def test_representation(self):
        day = WeekDay(1)
        assert repr(day) == "WeekDay(1)"

    @pytest.mark.parametrize(
        ('index', 'first_week_day', 'position'),
        [
            (0, 0, 0),
            (1, 0, 1),
            (6, 0, 6),
            (0, 6, 1),
            (1, 6, 2),
            (6, 6, 0),
        ]
    )
    def test_position(self, index, first_week_day, position):
        i18n.get_locale = flexmock(first_week_day=first_week_day)
        day = WeekDay(index)
        assert day.position == position

    def test_get_name_returns_localized_week_day_name(self):
        day = WeekDay(0)
        assert day.get_name() == 'maanantaina'

    def test_override_get_locale_as_class_method(self):
        day = WeekDay(0)
        assert day.get_name() == 'maanantaina'

    def test_name_delegates_to_get_name(self):
        day = WeekDay(0)
        flexmock(day).should_receive('get_name').and_return('maanantaina')
        assert day.name == 'maanantaina'

    def test_unicode(self):
        day = WeekDay(0)
        flexmock(day).should_receive('name').and_return('maanantaina')
        assert str(day) == 'maanantaina'

    def test_str(self):
        day = WeekDay(0)
        flexmock(day).should_receive('name').and_return('maanantaina')
        assert str(day) == 'maanantaina'


@pytest.mark.skipif('i18n.babel is None')
class TestWeekDays:
    def test_constructor_with_valid_bit_string(self):
        days = WeekDays('1000100')
        assert days._days == {WeekDay(0), WeekDay(4)}

    @pytest.mark.parametrize(
        'bit_string',
        [
            '000000',    # too short
            '00000000',  # too long
        ]
    )
    def test_constructor_with_bit_string_of_invalid_length(self, bit_string):
        with pytest.raises(ValueError):
            WeekDays(bit_string)

    def test_constructor_with_bit_string_containing_invalid_characters(self):
        with pytest.raises(ValueError):
            WeekDays('foobarz')

    def test_constructor_with_another_week_days_object(self):
        days = WeekDays('0000000')
        another_days = WeekDays(days)
        assert days._days == another_days._days

    def test_representation(self):
        days = WeekDays('0000000')
        assert repr(days) == "WeekDays('0000000')"

    @pytest.mark.parametrize(
        'bit_string',
        [
            '0000000',
            '1000000',
            '0000001',
            '0101000',
            '1111111',
        ]
    )
    def test_as_bit_string(self, bit_string):
        days = WeekDays(bit_string)
        assert days.as_bit_string() == bit_string

    def test_equality_with_equal_week_days_object(self):
        days = WeekDays('0001000')
        days2 = WeekDays('0001000')
        assert days == days2

    def test_equality_with_unequal_week_days_object(self):
        days = WeekDays('0001000')
        days2 = WeekDays('1000000')
        assert days != days2

    def test_equality_with_equal_bit_string(self):
        days = WeekDays('0001000')
        assert days == '0001000'

    def test_equality_with_unequal_bit_string(self):
        days = WeekDays('0001000')
        assert days != '0101000'

    def test_equality_with_unsupported_comparison(self):
        days = WeekDays('0001000')
        assert days != 0

    def test_iterator_starts_from_locales_first_week_day(self):
        i18n.get_locale = lambda: flexmock(first_week_day=1)
        days = WeekDays('1111111')
        indices = list(day.index for day in days)
        assert indices == [1, 2, 3, 4, 5, 6, 0]

    def test_unicode(self):
        i18n.get_locale = lambda: i18n.babel.Locale('fi')
        days = WeekDays('1000100')
        assert str(days) == 'maanantaina, perjantaina'

    def test_str(self):
        i18n.get_locale = lambda: i18n.babel.Locale('fi')
        days = WeekDays('1000100')
        assert str(days) == 'maanantaina, perjantaina'
