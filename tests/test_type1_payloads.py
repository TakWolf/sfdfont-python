import pytest

from sfdfont import SfdFont, SfdLimitError, SfdParseError, SfdReadLimits
from sfdfont._binary import payload
from sfdfont._reader import Reader, encode_ascii85
from sfdfont._writer import binary


def test_unterminated_type1_blocks_stop_after_declared_length():
    for header in (b'OrigType1: 5\n', b'BeginSubrs: 2\n3 2\n'):
        reader = Reader(header + encode_ascii85(b'abcde') + b'\nNext: value\n')
        item = payload(reader, reader.word())
        assert item.data == b'abcde'
        assert item.terminator == ''
        assert reader.word() == 'Next:'
        encoded = Reader(binary(item))
        assert payload(encoded, encoded.word()) == item
        assert not encoded.word()


@pytest.mark.parametrize('header', [b'OrigType1: 0\n', b'BeginSubrs: 0\n', b'BeginSubrs: 2 0 0\n'])
def test_empty_type1_payloads(header):
    reader = Reader(header + b'Next: value\n')
    item = payload(reader, reader.word())
    assert item.data == b''
    assert reader.word() == 'Next:'


@pytest.mark.parametrize(
    'data',
    [b'BeginSubrs: -1\n', b'BeginSubrs: 1 -1\n', b'BeginSubrs: 2 4\n', b'OrigType1: -1\n', b'OrigType1: 4\n'],
)
def test_invalid_type1_counts_and_truncation(data):
    reader = Reader(data)
    with pytest.raises(SfdParseError):
        payload(reader, reader.word())


def test_upstream_font_with_retained_legacy_payloads(assets_dir, tmp_path):
    data = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    subrs = b'BeginSubrs: 2 3 2\n' + encode_ascii85(b'abcde') + b'\n'
    original = b'OrigType1: 4\n' + encode_ascii85(b'\0\xff\0\x01') + b'\n'
    data = data.replace(b'BeginChars:', subrs + b'BeginChars:', 1)
    data = data.replace(b'\nWidth:', b'\n' + original + b'Width:', 1)
    font = SfdFont.parse(data)
    assert font.payloads[0].parameters == b'2 3 2'
    assert font.glyphs[0].payloads[0].data == b'\0\xff\0\x01'
    path = tmp_path.joinpath('BoxesAndBounds.sfd')
    font.save(path)
    assert SfdFont.load(path) == font
    with pytest.raises(SfdLimitError, match='max_payload_bytes'):
        SfdFont.parse(data, limits=SfdReadLimits(max_payload_bytes=8))
