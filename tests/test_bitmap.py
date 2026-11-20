import pytest

from sfdfont import SfdFont, SfdLimitError, SfdReadLimits
from sfdfont._reader import encode_ascii85


def document(strikes: bytes, version=b'3.2') -> bytes:
    return (
        b'SplineFontDB: ' + version + b'\nBeginChars: 256 1\n'
        b'StartChar: A\nEncoding: 65 65 7\nWidth: 600\nEndChar\nEndChars\n' + strikes + b'EndSplineFont\n'
    )


@pytest.mark.parametrize('depth', [1, 2, 4, 8])
def test_strike_samples_and_properties(depth):
    samples = b'\x80\x00' if depth == 1 else bytes([0, 1, 2, 3, 0, 1, 2, 3, 0])
    data = (
        f'BitmapFont: 12 8 10 2 {depth} Test\n'.encode()
        + b'BDFStartProperties: 2\nFONT 16 "test font"\nSIZE 18 12\nBDFEndProperties\n'
        + b'BDFChar: 7 65 6 0 8 -1 -1\n'
        + encode_ascii85(samples)
        + b'\nEndBitmapFont\n'
    )
    font = SfdFont.parse(document(data + data))
    assert len(font.bitmap_strikes) == 2
    strike = font.bitmap_strikes[0]
    assert strike.depth == depth
    assert strike.properties[0].value == 'test font'
    assert strike.properties[1].value == 12
    assert strike.glyphs[0].width == 9
    assert strike.glyphs[0].height == 1
    assert strike.pixels(strike.glyphs[0]) == ([[1] + [0] * 8] if depth == 1 else [list(samples)])


def test_old_bitmap_header_and_same_line_marker():
    data = b'BitmapFont: 12 256 10 2 BDFChar: 65 6 0 0 0 0\nz\nEndBitmapFont\n'
    font = SfdFont.parse(document(data, version=b'1.0'))
    strike = font.bitmap_strikes[0]
    assert strike.foundry is None
    assert strike.glyphs[0].glyph_id == 7
    assert strike.glyphs[0].data == b'\0'


def test_bitmap_reference_cycle():
    from sfdfont import SfdParseError

    with pytest.raises(SfdParseError, match='cyclic'):
        SfdFont.parse(
            document(b'BitmapFont: 12 8 10 2 1\nBDFChar: 7 65 6 0 0 0 0\nz\nBDFRefChar: 7 7 2 -3 N\nEndBitmapFont\n')
        )


def test_bitmap_payload_budget_before_allocation():
    with pytest.raises(SfdLimitError):
        SfdFont.parse(
            document(b'BitmapFont: 12 8 10 2 8\nBDFChar: 7 65 6 0 999999 0 999999\n'),
            limits=SfdReadLimits(max_payload_bytes=100),
        )
