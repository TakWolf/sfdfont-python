import io

import pytest

from sfdfont import (
    SfdBitmapGlyph,
    SfdBitmapStrike,
    SfdContour,
    SfdFont,
    SfdGlyph,
    SfdLayer,
    SfdPoint,
    SfdRecord,
    SfdReference,
    SfdValidationError,
)


def make_font():
    font = SfdFont()
    font.metadata.font_name = 'Test'
    font.metadata.comments = '中文😀 + = " \\ ~\nnext'
    font.glyphs = [
        SfdGlyph(
            'A',
            5,
            65,
            65,
            600,
            layers=[
                SfdLayer(
                    1,
                    [
                        SfdContour(
                            [
                                SfdPoint(0, 0),
                                SfdPoint(10.125, 20, 'l'),
                                SfdPoint(0, 0, 'l'),
                            ]
                        )
                    ],
                )
            ],
        ),
        SfdGlyph('A.alt', 8, -1, -1, 600, layers=[SfdLayer(1, references=[SfdReference(5, 65)])]),
    ]
    font.bitmap_strikes = [
        SfdBitmapStrike(
            12,
            10,
            2,
            glyphs=[
                SfdBitmapGlyph(5, 65, 6, 0, 8, -1, 0, b'\x80\0\x40\0'),
            ],
        )
    ]
    return font


def test_construct_edit_and_write(tmp_path):
    font = make_font()
    font.glyphs[0].width = 700
    font.metadata.comments = 'edited😀'
    path = tmp_path.joinpath('test.sfd')
    font.save(path)
    assert b'Width: 700\n' in path.read_bytes()
    output = io.BytesIO()
    font.dump(output)
    assert not output.closed
    assert output.getvalue() == path.read_bytes()


def test_opaque_records_preserved_and_edits_rejected(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    assert font.metadata.records
    font.glyphs[0].width += 1
    font.glyphs[0].layers[0].contours[0].points[0].x += 1
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()
    font.metadata.records.clear()
    for glyph in font.glyphs:
        glyph.records.clear()
        for layer in glyph.layers:
            layer.records.clear()
    assert b'Width: 379\n' in font.dump_to_bytes()


@pytest.mark.parametrize(
    'operation',
    [
        lambda f: setattr(f.glyphs[1], 'glyph_id', 5),
        lambda f: setattr(f.glyphs[1], 'encoding', 65),
        lambda f: setattr(f.glyphs[0], 'unicode', 0xD800),
        lambda f: setattr(f.glyphs[0], 'width', 32768),
        lambda f: setattr(f.glyphs[1].layers[0].references[0], 'target', 100),
        lambda f: f.glyphs[0].layers[0].references.append(SfdReference(8)),
        lambda f: setattr(f.bitmap_strikes[0].glyphs[0], 'data', b''),
        lambda f: setattr(f.metadata, 'font_name', 'bad\nname'),
        lambda f: f.metadata.records.append(SfdRecord('EndSplineFont', b'')),
    ],
)
def test_invalid_model_is_rejected_before_truncating_file(tmp_path, operation):
    font = make_font()
    operation(font)
    path = tmp_path.joinpath('keep.sfd')
    path.write_bytes(b'keep')
    with pytest.raises(SfdValidationError):
        font.save(path)
    assert path.read_bytes() == b'keep'


def test_short_writing_stream():
    class ShortWriter(io.BytesIO):
        def write(self, data):
            return super().write(data[:7])

    font = make_font()
    output = ShortWriter()
    font.dump(output)
    assert output.getvalue() == font.dump_to_bytes()


def test_long_reference_chain_does_not_use_python_recursion():
    font = SfdFont()
    font.glyphs = [SfdGlyph(str(i), i, layers=[SfdLayer(1, references=[SfdReference(i + 1)])]) for i in range(1500)]
    font.glyphs.append(SfdGlyph('end', 1500))
    font.validate()


def test_old_core_output():
    font = make_font()
    font.version = '1.0'
    data = font.dump_to_bytes()
    assert data.startswith(b'SplineFontDB: 1.0\n')
    assert b'Order2: 0\n' in data


@pytest.mark.parametrize('scope', ['font', 'glyph', 'layer'])
@pytest.mark.parametrize(
    ('keyword', 'value'),
    [
        ('Refer:', b'999 -1 N 1 0 0 1 0 0 0'),
        ('Ref:', b'65 -1 N 1 0 0 1 0 0 0'),
        ('AltUni:', b'66'),
        ('AltUni2:', b'000042.ffffffff.0'),
        ('Comments:', b'hello'),
        ('Width:', b'700'),
        ('GridOrder2:', b'1'),
        ('StartChar:', b'A'),
    ],
)
def test_structural_raw_records_are_rejected_before_saving(tmp_path, scope, keyword, value):
    font = SfdFont(glyphs=[SfdGlyph('A', 0, layers=[SfdLayer(1)])])
    items = {
        'font': font.metadata.records,
        'glyph': font.glyphs[0].records,
        'layer': font.glyphs[0].layers[0].records,
    }[scope]
    items.append(SfdRecord(keyword, value))
    with pytest.raises(SfdValidationError, match='structural'):
        font.validate()
    path = tmp_path.joinpath('keep.sfd')
    path.write_bytes(b'keep')
    with pytest.raises(SfdValidationError, match='structural'):
        font.save(path)
    assert path.read_bytes() == b'keep'


def test_unknown_raw_records_still_roundtrip_in_all_scopes():
    font = SfdFont(glyphs=[SfdGlyph('A', 0, layers=[SfdLayer(1)])])
    for items in (font.metadata.records, font.glyphs[0].records, font.glyphs[0].layers[0].records):
        items.append(SfdRecord('Unknown:', b'preserved'))
    assert SfdFont.parse(font.dump_to_bytes()) == font
