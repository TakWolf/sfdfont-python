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


def test_construct_edit_and_semantic_roundtrip(tmp_path):
    font = make_font()
    data = font.dump_to_bytes()
    parsed = SfdFont.parse(data)
    assert parsed == font
    assert parsed.dump_to_bytes() == data
    parsed.glyphs[0].width = 700
    parsed.metadata.comments = 'edited😀'
    path = tmp_path.joinpath('test.sfd')
    parsed.save(path)
    assert SfdFont.load(path) == parsed
    output = io.BytesIO()
    parsed.dump(output)
    assert not output.closed
    assert output.getvalue() == path.read_bytes()


def test_opaque_records_preserved_and_edits_rejected():
    font = make_font()
    font.metadata.records.append(SfdRecord('FutureExtension:', b'123'))
    parsed = SfdFont.parse(font.dump_to_bytes())
    assert parsed.dump_to_bytes() == font.dump_to_bytes()
    parsed.glyphs[0].width += 1
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        parsed.dump_to_bytes()
    parsed.metadata.records.clear()
    assert SfdFont.parse(parsed.dump_to_bytes()) == parsed


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
    assert SfdFont.parse(font.dump_to_bytes()) == font
