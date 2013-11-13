from pytest import raises
from sqlalchemy_utils.primitives import NumberRange, NumberRangeException


class TestNumberRangeInit(object):
    def test_support_range_object(self):
        num_range = NumberRange(NumberRange(1, 3))
        assert num_range.lower == 1
        assert num_range.upper == 3

    def test_supports_multiple_args(self):
        num_range = NumberRange(1, 3)
        assert num_range.lower == 1
        assert num_range.upper == 3

    def test_supports_strings(self):
        num_range = NumberRange('1-3')
        assert num_range.lower == 1
        assert num_range.upper == 3

    def test_supports_strings_with_spaces(self):
        num_range = NumberRange('1 - 3')
        assert num_range.lower == 1
        assert num_range.upper == 3

    def test_supports_strings_with_bounds(self):
        num_range = NumberRange('[1, 3]')
        assert num_range.lower == 1
        assert num_range.upper == 3

    def test_supports_exact_ranges_as_strings(self):
        num_range = NumberRange('3')
        assert num_range.lower == 3
        assert num_range.upper == 3

    def test_supports_integers(self):
        num_range = NumberRange(3)
        assert num_range.lower == 3
        assert num_range.upper == 3


class TestComparisonOperators(object):
    def test_eq_operator(self):
        assert NumberRange(1, 3) == NumberRange(1, 3)
        assert not NumberRange(1, 3) == NumberRange(1, 4)

    def test_ne_operator(self):
        assert not NumberRange(1, 3) != NumberRange(1, 3)
        assert NumberRange(1, 3) != NumberRange(1, 4)

    def test_gt_operator(self):
        assert NumberRange(1, 3) > NumberRange(0, 2)
        assert not NumberRange(2, 3) > NumberRange(2, 3)

    def test_ge_operator(self):
        assert NumberRange(1, 3) >= NumberRange(0, 2)
        assert NumberRange(1, 3) >= NumberRange(1, 3)

    def test_lt_operator(self):
        assert NumberRange(0, 2) < NumberRange(1, 3)
        assert not NumberRange(2, 3) < NumberRange(2, 3)

    def test_le_operator(self):
        assert NumberRange(0, 2) <= NumberRange(1, 3)
        assert NumberRange(1, 3) >= NumberRange(1, 3)

    def test_integer_comparison(self):
        assert NumberRange(2, 2) <= 3
        assert NumberRange(1, 3) >= 0
        assert NumberRange(2, 2) == 2
        assert NumberRange(2, 2) != 3


def test_str_representation():
    assert str(NumberRange(1, 3)) == '1 - 3'
    assert str(NumberRange(1, 1)) == '1'


def test_raises_exception_for_badly_constructed_range():
    with raises(NumberRangeException):
        NumberRange(3, 2)


class TestArithmeticOperators(object):
    def test_add_operator(self):
        assert NumberRange(1, 2) + NumberRange(1, 2) == NumberRange(2, 4)

    def test_sub_operator(self):
        assert NumberRange(1, 3) - NumberRange(1, 2) == NumberRange(-1, 2)

    def test_isub_operator(self):
        range_ = NumberRange(1, 3)
        range_ -= NumberRange(1, 2)
        assert range_ == NumberRange(-1, 2)

    def test_iadd_operator(self):
        range_ = NumberRange(1, 2)
        range_ += NumberRange(1, 2)
        assert range_ == NumberRange(2, 4)
