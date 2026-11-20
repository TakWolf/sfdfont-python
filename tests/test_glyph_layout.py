import pytest

from sfdfont import (
    SfdAnchor,
    SfdAnchorClass,
    SfdAnchorClasses,
    SfdFont,
    SfdGlyph,
    SfdKerningPair,
    SfdKerningPairs,
    SfdLigatureCarets,
    SfdLookup,
    SfdLookupSubtable,
    SfdPairPosition,
    SfdParseError,
    SfdPosition,
    SfdPositionValue,
    SfdRecord,
    SfdSubstitution,
    SfdValidationError,
)
from sfdfont._parser import record
from sfdfont._reader import Reader
from sfdfont._writer import records


@pytest.mark.parametrize(
    ('data', 'factory'),
    [
        ('Position2: "pos" dx=10 dy=-20 dh=30 dv=0 [ddx={12-13 1,-1} ddy={} ddh={} ddv={}]', SfdPosition),
        ('PairPos2: "pair" 字形 dx=0 dy=0 dh=-20 dv=0 dx=0 dy=0 dh=0 dv=10 [ddv={12-12 1}]', SfdPairPosition),
        ('Substitution2: "single" B', SfdSubstitution),
        ('MultipleSubs2: "multiple"', SfdSubstitution),
        ('AlternateSubs2: "alternate" A B', SfdSubstitution),
        ('Ligature2: "ligature" f f i', SfdSubstitution),
        ('LCarets2: 3 100 200 300', SfdLigatureCarets),
        ('AnchorPoint: "above" 10.5 -20 baselig 2 {12-13 0,1} {} 10', SfdAnchor),
        ('AnchorClass2: "above" "marks" "entry" "" 1', SfdAnchorClasses),
        ('Kerns2: 1 -20 "pair" {12-13 1,0} 2 10 "pair"', SfdKerningPairs),
    ],
)
def test_glyph_layout_record_models(data, factory):
    reader = Reader(data.encode())
    item = record(reader, reader.word())
    assert not reader.word()
    model = factory.from_record(item)
    assert factory.from_record(model.to_record()) == model
    assert model.copy() == model.deepcopy() == model
    assert records([item])


def test_position_default_values_and_copying():
    pair = SfdPairPosition('pair', 'B')
    assert pair.first is not pair.second
    assert pair.first.x_adjustments is not pair.second.x_adjustments
    assert pair.copy().first is pair.first
    assert pair.deepcopy().first is not pair.first
    values = {}
    position = SfdPositionValue(x_adjustments=values)
    assert position.x_adjustments is values
    carets = []
    assert SfdLigatureCarets(carets).carets is carets


@pytest.mark.parametrize(
    'data',
    [
        b'Position2: "pos" dx=0 dy=0 dh=0',
        b'Position2: "pos" dx=0 dy=0 dh=0 dv=0 [ddx={} ddx={}]',
        b'PairPos2: "pair" B dx=0 dy=0 dh=0 dv=0',
        b'Substitution2: "single" A B',
        b'LCarets2: 2 100',
        b'AnchorPoint: "above" nan 0 mark 0',
        b'AnchorPoint: "above" 0 0 unknown 0',
        b'AnchorClass2: "a" "x" "a" "y"',
    ],
)
def test_malformed_glyph_layout(data):
    reader = Reader(data)
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


def modern_font():
    font = SfdFont(glyphs=[SfdGlyph('A'), SfdGlyph('B', 1)])
    font.set_lookup(SfdLookup(257, 'pos', subtables=[SfdLookupSubtable('position')]))
    font.set_lookup(
        SfdLookup(
            258,
            'pair',
            subtables=[SfdLookupSubtable('horizontal', vertical=False), SfdLookupSubtable('vertical', vertical=True)],
        )
    )
    font.set_lookup(SfdLookup(1, 'sub', subtables=[SfdLookupSubtable('single')]))
    font.set_lookup(SfdLookup(260, 'mark', subtables=[SfdLookupSubtable('marks')]))
    font.metadata.records.append(SfdAnchorClasses([SfdAnchorClass('above', 'marks')]).to_record())
    font.glyphs[0].records.extend(
        [
            SfdPosition('position', SfdPositionValue(x_advance=10)).to_record(),
            SfdPairPosition('horizontal', 'B', SfdPositionValue(x_advance=-20)).to_record(),
            SfdSubstitution(subtable='single', glyphs=['B']).to_record(),
            SfdLigatureCarets([200]).to_record(),
            SfdAnchor('above', 100, 700).to_record(),
            SfdKerningPairs(pairs=[SfdKerningPair(1, -20, 'horizontal')]).to_record(),
        ]
    )
    return font


def test_modern_glyph_layout_dependencies_and_pair_direction():
    font = modern_font()
    font.validate()
    font.glyphs[0].records[-1] = SfdKerningPairs('VKerns2:', [SfdKerningPair(1, -20, 'horizontal')]).to_record()
    with pytest.raises(SfdValidationError, match='direction'):
        font.validate()
    font.glyphs[0].records[-1] = SfdKerningPairs(pairs=[SfdKerningPair(20, -20, 'horizontal')]).to_record()
    with pytest.raises(SfdValidationError, match='dangling kerning'):
        font.validate()
    font.glyphs[0].records[-1] = SfdSubstitution(subtable='single', glyphs=['missing']).to_record()
    with pytest.raises(SfdValidationError, match='unknown glyph'):
        font.validate()


def test_glyph_layout_scope_and_versions():
    font = modern_font()
    font.metadata.records.append(SfdRecord('LCarets2:', b'0'))
    with pytest.raises(SfdValidationError, match='font metadata'):
        font.validate()
    font.metadata.records.pop()
    font.version = '1.0'
    with pytest.raises(SfdValidationError, match='version'):
        font.validate()


def test_edit_upstream_anchor_while_retaining_hints(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'DejaVuSerif.sfd'))
    changed = False
    for glyph in font.glyphs:
        for group in [glyph.records, *(layer.records for layer in glyph.layers)]:
            for index, item in enumerate(group):
                if item.keyword == 'AnchorPoint:':
                    anchor = SfdAnchor.from_record(item)
                    anchor.y += 20
                    group[index] = anchor.to_record()
                    changed = True
                    break
            if changed:
                break
        if changed:
            break
    assert changed
    path = tmp_path.joinpath('DejaVuSerif.sfd')
    font.save(path)
    assert SfdFont.load(path) == font
