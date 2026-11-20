import pytest

from sfdfont import SfdFont, SfdParseError
from sfdfont._parser import glyph, spline_set
from sfdfont._reader import Reader


def test_point_flags_use_bounded_integer_reader():
    reader = Reader(b'0 0 m ' + b'9' * 5000 + b'\nEndSplineSet\n')
    with pytest.raises(SfdParseError, match='integer exceeds supported field size'):
        spline_set(reader)
    point = spline_set(Reader(b'0 0 m 4294967295\nEndSplineSet\n'))[0].points[0]
    assert point.flags == 0xFFFFFFFF


@pytest.mark.parametrize('field', [0, 1, 2])
def test_altuni_hex_fields_are_bounded_before_conversion(field):
    fields = [b'000041', b'ffffffff', b'0']
    fields[field] = b'f' * 5000
    data = b'A\nEncoding: 0 65 0\nWidth: 600\nAltUni2: ' + b'.'.join(fields) + b'\nEndChar\n'
    with pytest.raises(SfdParseError, match='invalid AltUni2 entry'):
        glyph(Reader(data), SfdFont())


def test_altuni_boundaries_and_zero_padding():
    data = (
        b'A\nEncoding: 0 65 0\nWidth: 600\n'
        b'AltUni2: 0010ffff.ffffffff.7fffffff 0000000000000041.000000000000fe0f.0\nEndChar\n'
    )
    font = SfdFont()
    font.glyphs.append(glyph(Reader(data), font))
    font.validate()
    first, second = font.glyphs[0].alternate_unicodes
    assert (first.unicode, first.variation_selector, first.font_id) == (0x10FFFF, -1, 0x7FFFFFFF)
    assert (second.unicode, second.variation_selector, second.font_id) == (65, 0xFE0F, 0)
