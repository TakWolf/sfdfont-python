import pytest

from sfdfont import SfdFont, SfdOs2Mask, SfdOs2Vendor, SfdPanose, SfdParseError, SfdRecord, SfdValidationError
from sfdfont._os2 import OS2_KEYS, decode_os2


def test_panose_byte_values_and_copy_semantics():
    values = [2, 0, 255, 128, 0, 0, 0, 0, 0, 0]
    value = SfdPanose(values)
    assert value.values is values
    assert value.copy().values is values
    assert value.deepcopy().values is not values
    assert value.deepcopy() == value
    assert SfdPanose.from_record(value.to_record()) == value
    signed = SfdPanose.from_record(SfdRecord('Panose:', b'2 0 -1 -128 0 0 0 0 0 0'))
    assert signed == value
    assert SfdPanose().values == [0] * 10
    assert SfdPanose().values is not SfdPanose().values
    explicit = []
    assert SfdPanose(explicit).values is explicit


@pytest.mark.parametrize('key, count', [('OS2CodePages:', 2), ('OS2UnicodeRanges:', 4)])
def test_os2_mask_word_order_and_unknown_bits(key, count):
    words = [0x80000001, 0x04000002, 0xFFFFFFFF, 0x80000000][:count]
    expected = sum(word << (index * 32) for index, word in enumerate(words))
    value = SfdOs2Mask.from_record(SfdRecord(key, b'.'.join(f'{word:08x}'.encode() for word in words)))
    assert value.value == expected
    assert SfdOs2Mask.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value
    assert value.to_record().value.split(b'.')[0] == b'80000001'


def test_os2_mask_old_whitespace_and_signed_hex_forms():
    value = SfdOs2Mask.from_record(SfdRecord('OS2CodePages:', b'#ffffffff -1'))
    assert value.value == (1 << 64) - 1
    assert value.to_record().value == b'ffffffff.ffffffff'


@pytest.mark.parametrize('vendor', [b'PfEd', b'TakW', b'    ', b"A'BC", b'A\\BC', b'CLM\0', b'A\xffBC', b'A\nBC'])
def test_os2_vendor_exact_four_byte_tag(vendor):
    value = SfdOs2Vendor(vendor)
    assert SfdOs2Vendor.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value


@pytest.mark.parametrize(
    'item',
    [
        SfdRecord('Panose:', b'0 0 0 0 0 0 0 0 0'),
        SfdRecord('Panose:', b'0 0 0 0 0 0 0 0 0 0 0'),
        SfdRecord('Panose:', b'256 0 0 0 0 0 0 0 0 0'),
        SfdRecord('Panose:', b'-129 0 0 0 0 0 0 0 0 0'),
        SfdRecord('OS2CodePages:', b'1..2'),
        SfdRecord('OS2CodePages:', b'100000000.0'),
        SfdRecord('OS2CodePages:', b'-ffffffff.0'),
        SfdRecord('OS2UnicodeRanges:', b'1.2'),
        SfdRecord('OS2UnicodeRanges:', b'1.2.3.4.5'),
        SfdRecord('OS2Vendor:', b"'short'"),
        SfdRecord('OS2Vendor:', b"'ABC'"),
        SfdRecord('OS2Vendor:', b"'ABCD' Injected:"),
    ],
)
def test_invalid_os2_records(item):
    with pytest.raises(SfdParseError):
        decode_os2(item)


@pytest.mark.parametrize(
    'model',
    [
        SfdPanose([]),
        SfdPanose([256] * 10),
        SfdPanose([True] * 10),
        SfdOs2Mask('OS2CodePages:', 1 << 64),
        SfdOs2Mask(value=-1),
        SfdOs2Mask('Unknown:'),
        SfdOs2Vendor('汉字ab'),
        SfdOs2Vendor('short'),
        SfdOs2Vendor((1, 2)),
        SfdOs2Vendor(b'A\\\nB'),
    ],
)
def test_invalid_os2_models(model):
    with pytest.raises(SfdValidationError):
        model.to_record()


@pytest.mark.parametrize('name', ['BoxesAndBounds.sfd', 'NimbusLGCUni-Regular.sfd', 'DejaVuSerif.sfd'])
def test_upstream_os2_edits_preserve_other_records(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    for item in font.metadata.records:
        if item.keyword in OS2_KEYS:
            value = decode_os2(item)
            assert decode_os2(value.to_record()) == value
    replacements = [
        SfdPanose([2, 0, 6, 3, 0, 0, 0, 0, 0, 0]).to_record(),
        SfdOs2Mask('OS2CodePages:', 1).to_record(),
        SfdOs2Mask('OS2UnicodeRanges:', 3).to_record(),
        SfdOs2Vendor(b'TakW').to_record(),
    ]
    for item in replacements:
        indices = [i for i, record in enumerate(font.metadata.records) if record.keyword == item.keyword]
        if indices:
            font.metadata.records[indices[0]] = item
        else:
            font.metadata.records.append(item)
    assert SfdFont.parse(font.dump_to_bytes()) == font
    font.metadata.records.append(replacements[0].copy())
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.validate()


def test_binary_vendor_record_boundaries(assets_dir):
    from sfdfont._parser import record
    from sfdfont._reader import Reader
    from sfdfont._writer import records

    for vendor in (b'CLM\0', b'A\xffBC', b'A\nBC'):
        item = SfdOs2Vendor(vendor).to_record()
        reader = Reader(records([item]) + b'Next: 1\n')
        assert record(reader, reader.word()) == item
        assert reader.word() == 'Next:'
        source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
        source = source.replace(b"OS2Vendor: 'PfEd'", b'OS2Vendor: ' + item.value)
        font = SfdFont.parse(source)
        assert SfdFont.parse(font.dump_to_bytes()) == font
