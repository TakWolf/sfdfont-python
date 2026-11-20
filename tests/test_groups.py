import pytest

from sfdfont import (
    SfdCidInfo,
    SfdFont,
    SfdGlyph,
    SfdGlyphGroup,
    SfdGroupKerningPair,
    SfdParseError,
    SfdRecord,
    SfdValidationError,
)
from sfdfont._groups import decode_group, decode_group_pair
from sfdfont._parser import record
from sfdfont._reader import Reader


def test_glyph_group_models_and_utf7_names():
    glyphs = ['A', 'Aacute', 'uni4E00']
    value = SfdGlyphGroup('选择 😀', glyphs)
    assert value.glyphs is glyphs
    assert value.copy().glyphs is glyphs
    assert value.deepcopy().glyphs is not glyphs
    assert value.deepcopy() == value
    assert SfdGlyphGroup.from_record(value.to_record()) == value
    assert SfdGlyphGroup.from_record(SfdGlyphGroup().to_record()) == SfdGlyphGroup()
    assert SfdGlyphGroup().glyphs is not SfdGlyphGroup().glyphs


@pytest.mark.parametrize('key', ['GroupKern:', 'GroupVKern:'])
def test_group_pair_record_kind_and_integer_bounds(key):
    for offset in [-0x80000000, -80, 0, 0x7FFFFFFF]:
        value = SfdGroupKerningPair(key, 'public.kern1.A', 'V', offset)
        assert SfdGroupKerningPair.from_record(value.to_record()) == value
        assert value.copy() == value.deepcopy() == value


@pytest.mark.parametrize(
    'key, data',
    [
        ('Group:', b'"name"'),
        ('Group:', b'"name" "A" extra'),
        ('GroupKern:', b'"left" "right"'),
        ('GroupVKern:', b'"left" 10'),
        ('GroupKern:', b'"left" "right" 2147483648'),
        ('GroupKern:', b'"left" "right" -2147483649'),
        ('GroupKern:', b'"left" "right" 10 extra'),
    ],
)
def test_malformed_group_records(key, data):
    reader = Reader(key.encode() + b' ' + data + b'\n')
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


@pytest.mark.parametrize(
    'value',
    [
        SfdGlyphGroup('group', ['A B']),
        SfdGlyphGroup('group', ['']),
        SfdGlyphGroup('group', ['\ud800']),
        SfdGroupKerningPair('Unknown:', 'A', 'V'),
        SfdGroupKerningPair(offset=1 << 31),
    ],
)
def test_invalid_group_models(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


def test_raw_ufo_bindings_are_not_resolved_or_repaired():
    group = SfdGlyphGroup('external', ['not-in-this-font'])
    pair = SfdGroupKerningPair(left='external-class', right='also-external', offset=-80)
    font = SfdFont()
    font.metadata.records = [group.to_record(), pair.to_record(), pair.to_record()]
    font.validate()
    assert decode_group(font.metadata.records[0]) == group
    assert decode_group_pair(font.metadata.records[1]) == pair
    assert font.metadata.records[1] == font.metadata.records[2]


def test_upstream_raw_group_offset_edit_keeps_bindings(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    original = SfdFont.parse(source)
    name = original.glyphs[0].name
    group = SfdGlyphGroup('custom group', [name])
    pair = SfdGroupKerningPair(left=group.name, right=name, offset=-80)
    items = [group.to_record(), pair.to_record()]
    data = b''.join(item.keyword.encode() + b' ' + item.value + b'\n' for item in items)
    font = SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'GroupKern:')
    edited = SfdGroupKerningPair.from_record(font.metadata.records[index])
    edited.offset = -100
    font.metadata.records[index] = edited.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    edited.right = 'external-name'
    font.metadata.records[index] = edited.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


def test_group_scope_and_validation():
    item = SfdGlyphGroup('group', ['A']).to_record()
    font = SfdFont(glyphs=[SfdGlyph(records=[item])])
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()
    font = SfdFont(cid=SfdCidInfo(), subfonts=[SfdFont()])
    font.subfonts[0].metadata.records.append(item)
    with pytest.raises(SfdValidationError, match='CID layout'):
        font.validate()
    font = SfdFont()
    font.metadata.records.append(SfdRecord('GroupKern:', b'"left"'))
    with pytest.raises(SfdValidationError):
        font.validate()


def test_raw_group_bindings_protect_native_class_names(assets_dir):
    from sfdfont import SfdKerningClass, SfdLookup, SfdLookupSubtable

    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    original = SfdFont.parse(source)
    first, second = original.glyphs[:2]
    kern = SfdKerningClass(
        'KernClass3:',
        first_classes=[None, [first.name]],
        second_classes=[None, [second.name]],
        offsets=[[0, 0], [0, -80]],
        subtable='kern-sub',
        first_names=[None, 'public.kern1.A'],
        second_names=[None, 'public.kern2.V'],
    )
    items = [
        SfdLookup(258, 'kern', subtables=[SfdLookupSubtable('kern-sub')]).to_record(),
        kern.to_record(),
        SfdGroupKerningPair(left='public.kern1.A', right='public.kern2.V', offset=-80).to_record(),
    ]
    data = b''.join(item.keyword.encode() + b' ' + item.value + b'\n' for item in items)
    font = SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'KernClass3:')
    value = SfdKerningClass.from_record(font.metadata.records[index])
    value.offsets[1][1] = -100
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    value.first_names[1] = 'renamed'
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()
