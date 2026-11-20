import pytest

from sfdfont import SfdFont, SfdGlyph, SfdParseError, SfdValidationError
from sfdfont._parser import glyph
from sfdfont._reader import Reader


def read_glyph(data):
    reader = Reader(data)
    reader.next_gid = 0
    return glyph(reader, SfdFont())


def test_created_empty_glyph_retains_explicit_width_flag():
    font = SfdFont(glyphs=[SfdGlyph('space', encoding=32, unicode=32, width=600)])
    assert font.glyphs[0].flags == 'W'
    assert b'Flags: W\n' in font.dump_to_bytes()


def test_loaded_flags_and_absence_preserved():
    start = b'space\nEncoding: 32 32 0\nWidth: 600\n'
    assert read_glyph(start + b'Flags: HMWOI\nEndChar\n').flags == 'HMWOI'
    assert read_glyph(start + b'EndChar\n').flags == ''
    with pytest.raises(SfdParseError, match='duplicate'):
        read_glyph(start + b'Flags: W\nFlags: H\nEndChar\n')


def test_invalid_flags_rejected_before_write():
    font = SfdFont(glyphs=[SfdGlyph(flags='X')])
    with pytest.raises(SfdValidationError, match='flags'):
        font.dump_to_bytes()
