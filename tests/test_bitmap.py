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


def editable_bitmap_font():
    return SfdFont.parse(
        document(
            b'BitmapFont: 12 8 10 2 1 Test\n'
            b'BDFStartProperties: 2\nFONT 16 "test font"\nSIZE 18 12\nBDFEndProperties\n'
            b'BDFChar: 7 65 6 0 0 0 0\nz\nEndBitmapFont\n'
        )
    )


@pytest.mark.parametrize(
    ('target', 'attribute', 'value'),
    [
        ('glyph', 'encoding', -2),
        ('glyph', 'encoding', True),
        ('glyph', 'glyph_id', 7.0),
        ('glyph', 'vertical_advance', '6\nEndBitmapFont'),
        ('glyph', 'vertical_advance', False),
        ('strike', 'depth', True),
        ('strike', 'resolution', 72.5),
        ('strike', 'foundry', 'two words'),
        ('strike', 'foundry', '中文'),
        ('property', 'name', 'two words'),
        ('property', 'name', '中文'),
        ('property', 'type', 20),
        ('property', 'type', True),
        ('property', 'value', 'bad"value'),
        ('integer_property', 'value', True),
        ('integer_property', 'value', 12.5),
        ('reference', 'source', 7.0),
        ('reference', 'target', True),
        ('reference', 'x', 1.5),
        ('reference', 'y', '0\nEndBitmapFont'),
        ('reference', 'selected', 1),
    ],
)
def test_invalid_bitmap_fields_do_not_replace_destination(tmp_path, target, attribute, value):
    from sfdfont import SfdBitmapGlyph, SfdBitmapReference, SfdValidationError

    font = editable_bitmap_font()
    strike = font.bitmap_strikes[0]
    font.glyphs.append(font.glyphs[0].deepcopy())
    font.glyphs[1].glyph_id, font.glyphs[1].encoding = 8, 66
    strike.glyphs.append(SfdBitmapGlyph(8, 66, 6, 0, 0, 0, 0, b'\0'))
    strike.references.append(SfdBitmapReference(7, 8))
    item = {
        'glyph': strike.glyphs[0],
        'strike': strike,
        'property': strike.properties[0],
        'integer_property': strike.properties[1],
        'reference': strike.references[0],
    }[target]
    setattr(item, attribute, value)
    with pytest.raises(SfdValidationError, match='bitmap'):
        font.validate()
    path = tmp_path.joinpath('keep.sfd')
    path.write_bytes(b'keep')
    with pytest.raises(SfdValidationError, match='bitmap'):
        font.save(path)
    assert path.read_bytes() == b'keep'


@pytest.mark.parametrize('encoding', [-1, 0, 0x7FFFFFFF])
def test_bitmap_integer_boundaries_roundtrip(encoding):
    from sfdfont import SfdBitmapReference

    font = editable_bitmap_font()
    strike = font.bitmap_strikes[0]
    glyph = strike.glyphs[0]
    glyph.encoding = encoding
    glyph.vertical_advance = -0x80000000
    strike.resolution = 0x7FFFFFFF
    strike.properties[1].value = -0x80000000
    # A reference needs a distinct target; leave outlines and bitmap IDs aligned.
    other = font.glyphs[0].deepcopy()
    other.glyph_id, other.encoding = 8, 66
    font.glyphs.append(other)
    bitmap = glyph.deepcopy()
    bitmap.glyph_id = 8
    strike.glyphs.append(bitmap)
    strike.references.append(SfdBitmapReference(7, 8, -0x80000000, 0x7FFFFFFF, True))
    assert SfdFont.parse(font.dump_to_bytes()) == font
