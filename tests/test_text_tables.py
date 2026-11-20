import pytest

from sfdfont import SfdParseError
from sfdfont._parser import record
from sfdfont._reader import Reader
from sfdfont._writer import records


def parse_record(data):
    reader = Reader(data)
    item = record(reader, reader.word())
    assert not reader.word()
    return item


def test_private_lengths_preserve_whitespace_and_embedded_terminators():
    value = b'  (first\nEndPrivate\nlast)  '
    data = b'BeginPrivate: 1\nCustom ' + str(len(value)).encode() + b' ' + value + b'\nEndPrivate\n'
    item = parse_record(data)
    assert value in item.value
    assert parse_record(records([item])) == item
    with pytest.raises(SfdParseError):
        parse_record(data.replace(b'BeginPrivate: 1', b'BeginPrivate: 2'))
    with pytest.raises(SfdParseError):
        parse_record(data.replace(str(len(value)).encode(), str(len(value) + 2).encode(), 1))


def test_private_logical_length_excludes_continuation_escape():
    item = parse_record(b'BeginPrivate: 1\nBlueValues 6 [1\\\n 20]\nEndPrivate\n')
    assert b'[1\\\n 20]' in item.value
    assert parse_record(records([item])) == item


def test_short_table_word_counts_and_optional_cvt_names():
    for data in [
        b'ShortTable: cvt  2\n  -10 "stem" \n  20 "cap height"\nEndShort\n',
        b'ShortTable: maxp 2\n -1 20\nEndShort\n',
    ]:
        item = parse_record(data)
        assert parse_record(records([item])) == item
    with pytest.raises(SfdParseError):
        parse_record(b'ShortTable: cvt  2\n-10\nEndShort\n')


def test_instruction_text_keeps_original_indentation():
    item = parse_record(b'TtInstrs:\n  PUSHB_1\n    10\nEndTTInstrs\n')
    assert b'\n    10\n' in item.value
    assert parse_record(records([item])) == item
