import pytest

from sfdfont import SfdFont, SfdGaspRange, SfdGaspTable, SfdGlyph, SfdParseError, SfdRecord, SfdValidationError
from sfdfont._parser import record
from sfdfont._reader import Reader


def test_gasp_model_copy_and_unknown_flag_bits():
    ranges = [SfdGaspRange(8, 2), SfdGaspRange(65535, 0xFFFF)]
    value = SfdGaspTable(ranges, version=1)
    assert value.ranges is ranges
    assert SfdGaspTable.from_record(value.to_record()) == value
    assert value.copy().ranges is ranges
    assert value.deepcopy().ranges[0] is not ranges[0]
    assert value.deepcopy() == value
    assert ranges[0].copy() == ranges[0].deepcopy() == ranges[0]
    assert SfdGaspTable().ranges is not SfdGaspTable().ranges


def test_gasp_empty_and_partial_ranges_are_not_inferred():
    for value in [SfdGaspTable(), SfdGaspTable([SfdGaspRange(8, 2)], version=2)]:
        assert SfdGaspTable.from_record(value.to_record()) == value


@pytest.mark.parametrize(
    'data',
    [
        b'1 8 2',
        b'2 8 2 0',
        b'0 0 99',
        b'-1 0',
        b'32768 0',
        b'1 -1 2 0',
        b'1 65536 2 0',
        b'1 8 65536 0',
        b'0 32768',
        b'2 8 2 8 3 0',
        b'2 10 2 8 3 0',
        b'1 8 2 0junk',
    ],
)
def test_malformed_gasp_records(data):
    reader = Reader(b'GaspTable: ' + data + b'\n')
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


@pytest.mark.parametrize(
    'value',
    [
        SfdGaspTable([SfdGaspRange(-1)]),
        SfdGaspTable([SfdGaspRange(flags=65536)]),
        SfdGaspTable([SfdGaspRange(8), SfdGaspRange(8)]),
        SfdGaspTable(version=True),
    ],
)
def test_invalid_gasp_models(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


def test_upstream_gasp_edit_keeps_other_dependencies_protected(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    table = SfdGaspTable([SfdGaspRange(8, 2), SfdGaspRange(65535, 3)])
    font.metadata.records.append(table.to_record())
    loaded = SfdFont.parse(font.dump_to_bytes())
    index = next(i for i, item in enumerate(loaded.metadata.records) if item.keyword == 'GaspTable:')
    table = SfdGaspTable.from_record(loaded.metadata.records[index])
    table.version = 1
    table.ranges[0].ppem = 10
    table.ranges[1].flags = 15
    loaded.metadata.records[index] = table.to_record()
    assert SfdFont.parse(loaded.dump_to_bytes()) == loaded
    loaded.glyphs[0].layers[0].contours[0].points[0].x += 1
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        loaded.dump_to_bytes()


def test_gasp_validation_duplicate_and_scope():
    font = SfdFont()
    item = SfdGaspTable().to_record()
    font.metadata.records = [item, item.copy()]
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.validate()
    font.metadata.records = [SfdRecord('GaspTable:', b'1 8 2')]
    with pytest.raises(SfdValidationError):
        font.validate()
    font.metadata.records.clear()
    font.glyphs = [SfdGlyph(records=[item])]
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()
    with pytest.raises(SfdParseError):
        SfdGaspTable.from_record(SfdRecord('Unknown:', b'0 0'))
