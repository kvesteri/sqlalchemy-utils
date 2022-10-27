import pytest

from sqlalchemy_utils import Ltree


class TestLtree:
    def test_init(self):
        assert Ltree('path.path') == Ltree(Ltree('path.path'))

    def test_constructor_with_wrong_type(self):
        with pytest.raises(TypeError) as e:
            Ltree(None)
        assert str(e.value) == (
            "Ltree() argument must be a string or an Ltree, not 'NoneType'"
        )

    def test_constructor_with_invalid_code(self):
        with pytest.raises(ValueError) as e:
            Ltree('..')
        assert str(e.value) == "'..' is not a valid ltree path."

    @pytest.mark.parametrize(
        'code',
        (
            'path',
            'path.path',
            '1_.2',
            '_._',
        )
    )
    def test_validate_with_valid_codes(self, code):
        Ltree.validate(code)

    @pytest.mark.parametrize(
        'path',
        (
            '',
            '.',
            'path.',
            'path..path',
            'path.path..path',
            'path.path..',
            'path.äö',
        )
    )
    def test_validate_with_invalid_path(self, path):
        with pytest.raises(ValueError) as e:
            Ltree.validate(path)
        assert str(e.value) == (
            f"'{path}' is not a valid ltree path."
        )

    @pytest.mark.parametrize(
        ('path', 'length'),
        (
            ('path', 1),
            ('1.1', 2),
            ('1.2.3', 3)
        )
    )
    def test_length(self, path, length):
        assert len(Ltree(path)) == length

    @pytest.mark.parametrize(
        ('path', 'subpath', 'index'),
        (
            ('path.path', 'path', 0),
            ('1.2.3', '2.3', 1),
            ('1.2.3.4', '2.3', 1),
            ('1.2.3.4', '3.4', 2)
        )
    )
    def test_index(self, path, subpath, index):
        assert Ltree(path).index(subpath) == index

    @pytest.mark.parametrize(
        ('path', 'item_slice', 'result'),
        (
            ('path.path', 0, 'path'),
            ('1.1.2.3', slice(1, 3), '1.2'),
            ('1.1.2.3', slice(1, None), '1.2.3'),
        )
    )
    def test_getitem(self, path, item_slice, result):
        assert Ltree(path)[item_slice] == result

    @pytest.mark.parametrize(
        ('path', 'others', 'result'),
        (
            ('1.2.3', ['1.2.3', '1.2'], '1'),
            ('1.2.3.4.5', ['1.2.3', '1.2.3.4'], '1.2'),
            ('1.2.3.4.5', ['3.4', '1.2.3.4'], None),
            ('1.2', ['1.2.3', '1.2.4'], '1')
        )
    )
    def test_lca(self, path, others, result):
        assert Ltree(path).lca(*others) == result

    @pytest.mark.parametrize(
        ('path', 'other', 'result'),
        (
            ('1.2.3', '4.5', '1.2.3.4.5'),
            ('1', '1', '1.1'),
        )
    )
    def test_add(self, path, other, result):
        assert Ltree(path) + other == result

    @pytest.mark.parametrize(
        ('path', 'other', 'result'),
        (
            ('1.2.3', '4.5', '4.5.1.2.3'),
            ('1', '1', '1.1'),
        )
    )
    def test_radd(self, path, other, result):
        assert other + Ltree(path) == result

    @pytest.mark.parametrize(
        ('path', 'other', 'result'),
        (
            ('1.2.3', '4.5', '1.2.3.4.5'),
            ('1', '1', '1.1'),
        )
    )
    def test_iadd(self, path, other, result):
        ltree = Ltree(path)
        ltree += other
        assert ltree == result

    @pytest.mark.parametrize(
        ('path', 'other', 'result'),
        (
            ('1.2.3', '2', True),
            ('1.2.3', '3', True),
            ('1', '1', True),
            ('1', '2', False),
        )
    )
    def test_contains(self, path, other, result):
        assert (other in Ltree(path)) == result

    @pytest.mark.parametrize(
        ('path', 'other', 'result'),
        (
            ('1', '1.2.3', True),
            ('1.2', '1.2.3', True),
            ('1.2.3', '1.2.3', True),
            ('1.2.3', '1', False),
            ('1.2.3', '1.2', False),
            ('1', '1', True),
            ('1', '2', False),
        )
    )
    def test_ancestor_of(self, path, other, result):
        assert Ltree(path).ancestor_of(other) == result

    @pytest.mark.parametrize(
        ('path', 'other', 'result'),
        (
            ('1', '1.2.3', False),
            ('1.2', '1.2.3', False),
            ('1.2', '1.2.3', False),
            ('1.2.3', '1', True),
            ('1.2.3', '1.2', True),
            ('1.2.3', '1.2.3', True),
            ('1', '1', True),
            ('1', '2', False),
        )
    )
    def test_descendant_of(self, path, other, result):
        assert Ltree(path).descendant_of(other) == result

    def test_getitem_with_other_than_slice_or_in(self):
        with pytest.raises(TypeError):
            Ltree('1.2')['something']

    def test_index_raises_value_error_if_subpath_not_found(self):
        with pytest.raises(ValueError):
            Ltree('1.2').index('3')

    def test_equality_operator(self):
        assert Ltree('path.path') == 'path.path'
        assert 'path.path' == Ltree('path.path')
        assert Ltree('path.path') == Ltree('path.path')

    def test_non_equality_operator(self):
        assert Ltree('path.path') != 'path.'
        assert not (Ltree('path.path') != 'path.path')

    def test_hash(self):
        assert hash(Ltree('path')) == hash('path')

    def test_repr(self):
        assert repr(Ltree('path')) == "Ltree('path')"

    def test_str(self):
        ltree = Ltree('path.path')
        assert str(ltree) == 'path.path'
