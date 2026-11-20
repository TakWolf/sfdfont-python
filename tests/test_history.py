import pytest

from sfdfont import SfdFont, SfdLimitError, SfdParseError, SfdReadLimits
from sfdfont._parser import glyph, record
from sfdfont._reader import Reader
from sfdfont._writer import records


def history(operation=b'Width: 500\n', kind=7):
    return (
        b'UndoRedoHistory\nLayer: 1\nUndoes\nUndoOperation\nIndex: 0\n'
        + f'Type: {kind}\n'.encode()
        + b'WasModified: 0\nWasOrder2: 0\n'
        + operation
        + b'EndUndoOperation\nEndUndoes\nRedoes\nEndRedoes\nEndUndoRedoHistory\n'
    )


def parse_history(data, limits=None):
    reader = Reader(data, limits)
    result = record(reader, reader.word())
    assert not reader.word()
    return result


def test_history_framing_and_multiline_strings():
    data = history(b'Width: 500\nComment: "text\nEndUndoOperation\ninside string"\n', 1)
    item = parse_history(data)
    assert parse_history(records([item])) == item
    assert b'inside string' in item.value


def test_history_uses_explicit_layer():
    reader = Reader(b'A\nEncoding: 65 65 0\nWidth: 600\n' + history() + b'Fore\nEndChar\n')
    font = SfdFont()
    item = glyph(reader, font)
    assert [layer.index for layer in item.layers] == [1]
    assert item.layers[0].records[0].keyword == 'UndoRedoHistory'


def test_historical_points_and_binary_data_count_toward_limits():
    data = history(b'SplineSet\n0 0 m 0\n10 10 l 0\nEndSplineSet\n', 1)
    with pytest.raises(SfdLimitError, match='max_points'):
        parse_history(data, SfdReadLimits(max_points=1))
    data = history(b'TtfInstrs: 4\nz\nEndTtf\n', 12)
    with pytest.raises(SfdLimitError, match='max_payload_bytes'):
        parse_history(data, SfdReadLimits(max_payload_bytes=3))


@pytest.mark.parametrize(
    ('old', 'new'),
    [
        (b'Index: 0', b'Index: 2'),
        (b'WasModified: 0', b'WasModified: 2'),
        (b'EndUndoOperation\n', b''),
        (b'EndUndoRedoHistory\n', b''),
        (b'Width: 500', b'Unexpected: 500'),
    ],
)
def test_malformed_history_boundaries(old, new):
    with pytest.raises(SfdParseError):
        parse_history(history().replace(old, new))
