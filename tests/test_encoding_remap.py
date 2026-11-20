import pytest

from sfdfont import (
    SfdEncodingRange,
    SfdEncodingRemap,
    SfdFont,
    SfdGlyph,
    SfdLimitError,
    SfdParseError,
    SfdReadLimits,
    SfdRecord,
    SfdValidationError,
)
from sfdfont._parser import record
from sfdfont._reader import Reader


def test_remap_models_keep_order_overlap_and_empty_containers():
    ranges = [SfdEncodingRange(0x1000000, 0x10000FF, 256), SfdEncodingRange(0x1000000, 0x100007F, 512)]
    value = SfdEncodingRemap(ranges)
    assert value.ranges is ranges
    assert value.copy().ranges is ranges
    assert value.deepcopy().ranges[0] is not ranges[0]
    assert value.deepcopy() == value
    assert SfdEncodingRemap.from_records(iter(value.to_records())) == value
    assert SfdEncodingRemap.from_records(SfdEncodingRemap().to_records()) == SfdEncodingRemap()
    empty = []
    assert SfdEncodingRemap(empty).ranges is empty
    assert SfdEncodingRemap().ranges is not SfdEncodingRemap().ranges
    entry = ranges[0]
    assert entry.copy() == entry.deepcopy() == entry
    assert SfdEncodingRange.from_record(entry.to_record()) == entry


@pytest.mark.parametrize(
    'data, expected',
    [
        (b'0 ff 0', SfdEncodingRange()),
        (b'0x1000000 #10000ff 256', SfdEncodingRange(0x1000000, 0x10000FF, 256)),
        (b'#-1 0xffffffff 2147483647', SfdEncodingRange(0xFFFFFFFF, 0xFFFFFFFF, 0x7FFFFFFF)),
        (b'0 7fffffff 0', SfdEncodingRange(0, 0x7FFFFFFF, 0)),
    ],
)
def test_remap_uint32_codes_and_signed32_destination(data, expected):
    value = SfdEncodingRange.from_record(SfdRecord('Remap:', data))
    assert value == expected
    assert SfdEncodingRange.from_record(value.to_record()) == value


@pytest.mark.parametrize(
    'data',
    [
        b'ff 0 0',
        b'0 ff -1',
        b'0 ff 2147483647',
        b'0 80000000 0',
        b'0 ff 2147483648',
        b'0 fffffffff 0',
        b'-80000001 ff 0',
        b'0 gg 0',
        b'0 ff',
        b'0 ff 0 extra',
        b'0 ff ' + b'9' * 5000,
    ],
)
def test_malformed_remap_entries(data):
    with pytest.raises(SfdParseError):
        record(Reader(data), 'Remap:')


@pytest.mark.parametrize(
    'value',
    [
        SfdEncodingRange(-1),
        SfdEncodingRange(0, 0x100000000),
        SfdEncodingRange(5, 4),
        SfdEncodingRange(base=-1),
        SfdEncodingRange(0, 255, 0x7FFFFFFF),
        SfdEncodingRange(True),
    ],
)
def test_invalid_remap_models(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


@pytest.mark.parametrize(
    'items',
    [
        [],
        [SfdRecord('Remap:', b'0 ff 0')],
        [SfdRecord('RemapN:', b'1')],
        [SfdRecord('RemapN:', b'0'), SfdRecord('Remap:', b'0 ff 0')],
        [SfdRecord('RemapN:', b'0'), SfdRecord('RemapN:', b'0')],
        [SfdRecord('RemapN:', b'-1')],
        [SfdRecord('RemapN:', b'1 extra')],
    ],
)
def test_remap_declaration_count_and_order(items):
    with pytest.raises(SfdParseError):
        SfdEncodingRemap.from_records(items)
    if items:
        font = SfdFont()
        font.metadata.records.extend(items)
        with pytest.raises(SfdValidationError):
            font.validate()


def test_remap_declaration_uses_reader_limits_without_allocating():
    with pytest.raises(SfdLimitError, match='max_bytes'):
        record(Reader(b'100', SfdReadLimits(max_bytes=32)), 'RemapN:')


def test_remap_scope_and_interleaved_records():
    with pytest.raises(SfdValidationError, match='record in glyph'):
        SfdFont(glyphs=[SfdGlyph(records=[SfdRecord('RemapN:', b'0')])]).validate()
    items = [SfdRecord('RemapN:', b'1'), SfdRecord('Comment:', b'"interleaved"'), SfdEncodingRange().to_record()]
    font = SfdFont()
    font.metadata.records.extend(items)
    font.validate()
    assert SfdEncodingRemap.from_records(items) == SfdEncodingRemap([SfdEncodingRange()])


def test_upstream_with_remap_preserves_encoding_dependencies(assets_dir, tmp_path):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    data = b'RemapN: 1\nRemap: 1000000 10000ff 0\n'
    font = SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))
    original = SfdEncodingRemap.from_records(font.metadata.records)
    assert original.ranges == [SfdEncodingRange(0x1000000, 0x10000FF, 0)]
    # Normalize hexadecimal spelling while preserving semantics.
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'Remap:')
    font.metadata.records[index].value = b'0x1000000 0x10000ff 0'
    assert SfdFont.parse(font.dump_to_bytes()) == font
    font.glyphs[0].width += 10
    assert SfdFont.parse(font.dump_to_bytes()) == font
    original.ranges[0].base += 1
    font.metadata.records[index] = original.ranges[0].to_record()
    destination = tmp_path.joinpath('unchanged.sfd')
    destination.write_bytes(b'keep this data')
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.save(destination)
    assert destination.read_bytes() == b'keep this data'
