import pytest

from sfdfont import (
    SfdFont,
    SfdGlyphAssembly,
    SfdGlyphPart,
    SfdGlyphVariants,
    SfdMathKern,
    SfdMathKernEntry,
    SfdMathValue,
    SfdParseError,
    SfdRecord,
    SfdValidationError,
)
from sfdfont._parser import record
from sfdfont._reader import Reader
from sfdfont._writer import records


def parse_record(data):
    reader = Reader(data)
    result = record(reader, reader.word())
    assert not reader.word()
    return result


@pytest.mark.parametrize(
    ('data', 'factory'),
    [
        (b'ItalicCorrection: -20 {12-14 1,0,-1}\n', SfdMathValue),
        (b'MATH:AxisHeight: 250 {}\n', SfdMathValue),
        (b'GlyphCompositionVertical: 2 base%0,0,10,100\n extender%1,20,20,50\n', SfdGlyphAssembly),
        (b'GlyphVariantsHorizontal: base larger largest\n', SfdGlyphVariants),
        (b'TopRightVertex: 2 100{12-13 1,0},-20 0,-30{12-13 -1,1}\n', SfdMathKern),
    ],
)
def test_math_record_models(data, factory):
    encoded = parse_record(data)
    model = factory.from_record(encoded)
    assert factory.from_record(model.to_record()) == model
    assert parse_record(records([encoded])) == encoded
    assert model == model.copy() == model.deepcopy()


def test_math_model_containers_and_copying():
    parts = []
    assembly = SfdGlyphAssembly(parts=parts)
    assert assembly.parts is parts
    parts.append(SfdGlyphPart('base'))
    assert assembly.copy().parts is parts
    assert assembly.deepcopy().parts[0] is not parts[0]
    assert SfdMathValue().adjustments is not SfdMathValue().adjustments
    assert SfdMathKernEntry().height_adjustments is not SfdMathKernEntry().height_adjustments
    with pytest.raises(SfdValidationError, match='contiguous'):
        SfdMathValue(adjustments={12: 1, 14: -1}).to_record()
    with pytest.raises(SfdValidationError, match='connector'):
        SfdGlyphAssembly(parts=[SfdGlyphPart('base', start_connector=20, full_advance=10)]).to_record()


@pytest.mark.parametrize(
    'data',
    [
        b'GlyphCompositionVertical: 2 base%0,0,0,10\n',
        b'GlyphCompositionHorizontal: 1 base%3,0,0,10\n',
        b'BottomLeftVertex: 2 100,-10\n',
        b'ItalicCorrection: 40 {12-14 1,2}\n',
        b'IsExtendedShape: 2\n',
    ],
)
def test_malformed_math_records(data):
    with pytest.raises(SfdParseError):
        parse_record(data)


def test_math_edits_with_retained_upstream_records(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    name = font.glyphs[1].name
    font.metadata.records.append(SfdMathValue('MATH:AxisHeight:', 250).to_record())
    font.glyphs[0].records.extend(
        [
            SfdMathValue(value=20).to_record(),
            SfdGlyphVariants(glyphs=[name]).to_record(),
            SfdGlyphAssembly(parts=[SfdGlyphPart(name, True, 20, 20, 100)]).to_record(),
            SfdMathKern(entries=[SfdMathKernEntry(100, -10)]).to_record(),
        ]
    )
    path = tmp_path.joinpath('BoxesAndBounds.sfd')
    font.save(path)
    assert SfdFont.load(path) == font
    font.glyphs[0].records[-2] = SfdGlyphAssembly(parts=[SfdGlyphPart('missing')]).to_record()
    with pytest.raises(SfdValidationError, match='unknown MATH glyph'):
        font.validate()


def test_math_scope_and_duplicate_fields():
    font = SfdFont()
    font.metadata.records.append(SfdMathValue(value=10).to_record())
    with pytest.raises(SfdValidationError, match='font metadata'):
        font.validate()
    font.metadata.records.clear()
    from sfdfont import SfdGlyph

    font.glyphs.append(SfdGlyph(records=[SfdRecord('IsExtendedShape:', b'1')] * 2))
    with pytest.raises(SfdValidationError, match='duplicate glyph MATH'):
        font.validate()
