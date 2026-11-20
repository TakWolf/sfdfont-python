import pytest

from sfdfont import SfdFont, SfdFontMetric, SfdParseError, SfdRecord, SfdSfntRevision, SfdValidationError


@pytest.mark.parametrize('keyword', ['CreationTime:', 'ModificationTime:'])
def test_timestamp_full_signed_64_bit_storage(keyword):
    for number in [-0x8000000000000000, -1, 0, 1 << 40, 0x7FFFFFFFFFFFFFFF]:
        value = SfdFontMetric(keyword, number)
        assert SfdFontMetric.from_record(value.to_record()) == value
    for number in [-0x8000000000000001, 0x8000000000000000]:
        with pytest.raises(SfdValidationError):
            SfdFontMetric(keyword, number).to_record()
        with pytest.raises(SfdParseError):
            SfdFontMetric.from_record(SfdRecord(keyword, str(number).encode()))
    with pytest.raises(SfdParseError):
        SfdFontMetric.from_record(SfdRecord(keyword, b'9' * 10000))


@pytest.mark.parametrize('keyword', ['UseUniqueID:', 'UseXUID:', 'NeedsXUIDChange:'])
def test_unique_identifier_flags_are_boolean_integers(keyword):
    for number in [0, 1]:
        value = SfdFontMetric(keyword, number)
        assert SfdFontMetric.from_record(value.to_record()) == value
    with pytest.raises(SfdValidationError):
        SfdFontMetric(keyword, 2).to_record()


@pytest.mark.parametrize('number', [-0x80000000, -1, 0, 0x7FFFFFFF])
def test_unique_identifier_uses_native_signed_storage(number):
    value = SfdFontMetric('UniqueID:', number)
    assert SfdFontMetric.from_record(value.to_record()) == value


@pytest.mark.parametrize('bits', [0, 0x00018000, 0x44445555, 0x80000000, 0xFFFFFFFF])
def test_sfnt_revision_bit_pattern_and_unset_sentinel(bits):
    value = SfdSfntRevision(bits)
    assert SfdSfntRevision.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value


@pytest.mark.parametrize('data, bits', [(b'-1', 0xFFFFFFFF), (b'#00018000', 0x18000), (b'-80000000', 0x80000000)])
def test_historical_sfnt_revision_hex_spellings(data, bits):
    assert SfdSfntRevision.from_record(SfdRecord('sfntRevision:', data)).value == bits


@pytest.mark.parametrize('data', [b'100000000', b'-ffffffff', b'1.5', b'0x' + b'f' * 10000, b'0x1 extra'])
def test_invalid_sfnt_revision_records(data):
    with pytest.raises(SfdParseError):
        SfdSfntRevision.from_record(SfdRecord('sfntRevision:', data))


def test_invalid_revision_model_and_wrong_kind():
    for number in [-1, 1 << 32, True]:
        with pytest.raises(SfdValidationError):
            SfdSfntRevision(number).to_record()
    with pytest.raises(SfdParseError):
        SfdSfntRevision.from_record(SfdRecord('Unknown:', b'0'))


def test_upstream_header_info_edit_does_not_refresh_timestamps(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    font.metadata.set_metric(SfdFontMetric('CreationTime:', 1 << 40))
    font.metadata.set_metric(SfdFontMetric('ModificationTime:', -1))
    font.metadata.set_metric(SfdFontMetric('UniqueID:', 1234567))
    font.metadata.records.append(SfdSfntRevision(0x44445555).to_record())
    loaded = SfdFont.parse(font.dump_to_bytes())
    assert loaded == font
    assert loaded.metadata.find_metric('CreationTime:').value == 1 << 40
    assert loaded.metadata.find_metric('ModificationTime:').value == -1
