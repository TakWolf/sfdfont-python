import pytest

from sfdfont import (
    SfdFont,
    SfdLegacyAnchorClasses,
    SfdLegacyBinding,
    SfdLegacyKerningPair,
    SfdLegacyKerningPairs,
    SfdLegacyPst,
    SfdParseError,
    SfdPositionValue,
    SfdValidationError,
)
from sfdfont._legacy_layout import LEGACY_KEYS, decode
from sfdfont._parser import record
from sfdfont._reader import Reader


@pytest.mark.parametrize(
    'data',
    [
        b'Ligature: f i',
        b"AlternateSubs: 0 'swsh' G.swash",
        b"Substitution: 0 65534 'subs' B",
        b'MultipleSubs: 0 0 <1,2> A B',
        b"Position: 0 65534 'test' dx=50 dy=0 dh=25 dv=0 [ddx={12-13 1,0}]",
        b"PairPos: 0 0 'dist' C dx=0 dy=10 dh=0 dv=0 | dx=0 dy=-20 dh=0 dv=0",
        b"LCarets: 0 '    ' 2 100 200",
        b'LCarets: 0 0 2 100 200',
        b'Kerns: 65 -20 66 10',
        b'KernsSLI: 65 -20 0',
        b'KernsSLIF: 65 -20 0 8 {12-13 1,-1}',
        b'VKernsSLIFO: 2 -20 0 0',
        b'AnchorClass: "above" mark 0 0 1 0 "above-mark" mkmk 0 0 2 1',
        b'AnchorClass: "above" 0',
    ],
)
def test_legacy_record_models(data):
    reader = Reader(data)
    item = record(reader, reader.word())
    assert not reader.word()
    value = decode(item, LEGACY_KEYS)
    assert decode(value.to_record(), LEGACY_KEYS) == value
    assert value.copy() == value.deepcopy() == value


def test_binding_omissions_and_ambiguous_prefixes():
    bare = SfdLegacyPst(glyphs=['f', 'i'])
    assert bare.to_record().value == b'f i'
    assert bare.copy().binding is bare.binding
    assert bare.deepcopy().binding is not bare.binding
    with pytest.raises(SfdValidationError):
        SfdLegacyPst(glyphs=['1', 'A']).to_record()
    with pytest.raises(SfdValidationError, match='preceding'):
        SfdLegacyPst(binding=SfdLegacyBinding(script_language_index=0), glyphs=['f', 'i']).to_record()
    with pytest.raises(SfdValidationError):
        SfdLegacyPst('LCarets:', carets=[200]).to_record()
    assert SfdLegacyPst('LCarets:', binding=SfdLegacyBinding(tag='    '), carets=[200]).to_record()
    pairs = SfdLegacyKerningPairs(pairs=[SfdLegacyKerningPair(65, -10, flags=0)])
    with pytest.raises(SfdValidationError, match='flags field'):
        pairs.to_record()


@pytest.mark.parametrize(
    'data',
    [
        b'KernsSLI: 65 -20',
        b'KernsSLIF: 65 -20 0',
        b"Position: 0 0 'test' dx=10 dy=0 dh=0",
        b"LCarets: 0 '    ' 2 100",
        b'AnchorClass: "above" toolong',
    ],
)
def test_malformed_legacy_records(data):
    reader = Reader(data)
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


@pytest.mark.parametrize(
    'name',
    ['AmbrosiaBold.sfd', 'ItalicHand.sfd', 'VKern.sfd', 'DejaVuSerif.sfd', 'NimbusLGCUni-Regular.sfd', 'Caliban.sfd'],
)
def test_upstream_legacy_models(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    groups = [
        font.metadata.records,
        *(g.records for g in font.glyphs),
        *(layer.records for g in font.glyphs for layer in g.layers),
    ]
    seen = 0
    for group in groups:
        for item in group:
            if item.keyword in LEGACY_KEYS:
                value = decode(item, LEGACY_KEYS)
                assert decode(value.to_record(), LEGACY_KEYS) == value
                seen += 1
    assert seen


def test_edit_upstream_legacy_pair_and_kerning_preserves_bindings(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'VKern.sfd'))
    groups = [*(g.records for g in font.glyphs), *(layer.records for g in font.glyphs for layer in g.layers)]
    pair_group, pair_index = next(
        (group, i) for group in groups for i, item in enumerate(group) if item.keyword == 'PairPos:'
    )
    pair = SfdLegacyPst.from_record(pair_group[pair_index])
    assert pair.pair_separator
    pair.positions[0].y_offset += 5
    pair.positions[1].y_offset -= 5
    pair_group[pair_index] = pair.to_record()
    kern_group, kern_index = next(
        (group, i) for group in groups for i, item in enumerate(group) if item.keyword == 'KernsSLIF:'
    )
    kern = SfdLegacyKerningPairs.from_record(kern_group[kern_index])
    kern.pairs[0].offset -= 10
    kern_group[kern_index] = kern.to_record()
    path = tmp_path.joinpath('VKern.sfd')
    font.save(path)
    assert SfdFont.load(path) == font
    pair.binding.tag = 'test'
    pair_group[pair_index] = pair.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.save(path)


def test_legacy_anchor_class_optional_fields(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'DejaVuSerif.sfd'))
    record = next(item for item in font.metadata.records if item.keyword == 'AnchorClass:')
    classes = SfdLegacyAnchorClasses.from_record(record)
    assert classes.classes[0].feature_tag == 'mark'
    assert classes.classes[0].merge_with == 1
    assert SfdLegacyAnchorClasses.from_record(classes.to_record()) == classes


def test_legacy_position_authoring():
    position = SfdLegacyPst('Position:', SfdLegacyBinding(0, 0, 'dist'), positions=[SfdPositionValue(x_advance=10)])
    assert SfdLegacyPst.from_record(position.to_record()) == position
