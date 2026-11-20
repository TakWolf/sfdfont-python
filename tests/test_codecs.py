import io

import pytest

from sfdfont._reader import Reader, encode_ascii85
from sfdfont._strings import decode_utf7, encode_utf7
from sfdfont.error import SfdLimitError, SfdParseError
from sfdfont.limits import SfdReadLimits


@pytest.mark.parametrize(
    ('text', 'encoded'),
    [
        ('中', b'+Ti0A'),
        ('😀', b'+2D3eAAAA'),
        ('+', b'+-'),
        ('=', b'+AD0A'),
        ('中文😀 + = " \\ ~', b'+Ti1lh9g93gAA +- +AD0A +ACIA +AFwA +AH4A'),
    ],
)
def test_fontforge_strings(text, encoded):
    assert decode_utf7(encoded) == text
    assert encode_utf7(text) == encoded


@pytest.mark.parametrize('text', ['éABC', '中-文', '中文+', '😀a', '汉字\n换行', '\t\r\\"~=', ''])
def test_string_boundaries(text):
    assert decode_utf7(encode_utf7(text)) == text


@pytest.mark.parametrize('data', [b'+', b'+A', b'+////', b'+2D0A'])
def test_invalid_strings(data):
    with pytest.raises(SfdParseError):
        decode_utf7(data)


@pytest.mark.parametrize('length', range(20))
def test_ascii85_boundaries(length):
    data = bytes(range(length))
    reader = Reader(encode_ascii85(data) + b'\nEndPayload')
    assert reader.ascii85(length) == data
    assert reader.word() == 'EndPayload'


def test_ascii85_backslash_newline_is_not_continuation():
    reader = Reader(b'!!!!\\\n!!!!!\nEnd')
    assert reader.ascii85(8) == b'\0\0\0;\0\0\0\0'
    assert reader.word() == 'End'


def test_ascii85_errors_and_limits():
    for data in (b'!!!!', b'uuuuu', b'y!!!!'):
        with pytest.raises(SfdParseError):
            Reader(data).ascii85(4)
    with pytest.raises(SfdLimitError):
        Reader(b'z', SfdReadLimits(max_payload_bytes=3)).ascii85(4)
    with pytest.raises(SfdLimitError):
        Reader(io.BytesIO(b'abcd'), SfdReadLimits(max_bytes=3))


def test_logical_lines_and_position():
    reader = Reader(b'FontName: Ex\\\nample\r\nBad')
    assert reader.word() == 'FontName:'
    assert reader.line() == b'Example'
    with pytest.raises(SfdParseError) as caught:
        reader.fail('test')
    assert caught.value.line == 3


def test_escaped_backslash_before_physical_newline():
    reader = Reader(b' line one\\nline two\\\\\nNext: value\n')
    assert reader.escaped_line() == b'line one\nline two\\'
    assert reader.word() == 'Next:'
