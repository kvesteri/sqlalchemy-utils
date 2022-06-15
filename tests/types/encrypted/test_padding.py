import pytest

from sqlalchemy_utils.types.encrypted.padding import (
    InvalidPaddingError,
    PKCS5Padding
)


class TestPkcs5Padding:
    def setup_method(self):
        self.BLOCK_SIZE = 8
        self.padder = PKCS5Padding(self.BLOCK_SIZE)

    def test_various_lengths_roundtrip(self):
        for number in range(0, 3 * self.BLOCK_SIZE):
            val = b'*' * number
            padded = self.padder.pad(val)
            unpadded = self.padder.unpad(padded)
            assert val == unpadded, 'Round trip error for length %d' % number

    def test_invalid_unpad(self):
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad(None)
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad(b'')
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad(b'\01')
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad((b'*' * (self.BLOCK_SIZE - 1)) + b'\00')
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad((b'*' * self.BLOCK_SIZE) + b'\01')

    def test_pad_longer_than_block(self):
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad(
                'x' * (self.BLOCK_SIZE - 1) +
                chr(self.BLOCK_SIZE + 1) * (self.BLOCK_SIZE + 1)
            )

    def test_incorrect_padding(self):
        # Hard-coded for blocksize of 8
        assert self.padder.unpad(b'1234\04\04\04\04') == b'1234'
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad(b'1234\02\04\04\04')
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad(b'1234\04\02\04\04')
        with pytest.raises(InvalidPaddingError):
            self.padder.unpad(b'1234\04\04\02\04')
