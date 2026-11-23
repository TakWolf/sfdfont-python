import pytest

from sfdfont import (
    SfdContour,
    SfdFont,
    SfdFontText,
    SfdGlyph,
    SfdLayer,
    SfdMetadata,
    SfdParseError,
    SfdPoint,
    SfdRecord,
    SfdValidationError,
)
from sfdfont._font_text import FONT_TEXT_KEYS


@pytest.mark.parametrize('keyword', sorted(FONT_TEXT_KEYS))
@pytest.mark.parametrize('text', ['', 'Family Name', '中文 😀', '"literal quotes"', '[1021 655 56001077 4734436]'])
def test_font_text_model_roundtrip_and_copy(keyword, text):
    value = SfdFontText(keyword, text)
    assert SfdFontText.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value
    assert value.copy() is not value
    assert repr(value).startswith('SfdFontText(')


@pytest.mark.parametrize(
    'value',
    [
        SfdFontText('Unknown:', 'value'),
        SfdFontText(text=b'bytes'),
        SfdFontText(text=' leading'),
        SfdFontText(text='trailing\t'),
        SfdFontText(text='bad\0value'),
        SfdFontText(text='bad\rvalue'),
        SfdFontText(text='bad\nvalue'),
        SfdFontText(text='ending\\'),
        SfdFontText(text='\ud800'),
    ],
)
def test_font_text_model_rejects_unrepresentable_values(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


@pytest.mark.parametrize('data', [b'bad\0value', b'bad\rvalue', b'bad\nvalue'])
def test_font_text_record_rejects_invalid_line_values(data):
    with pytest.raises(SfdParseError):
        SfdFontText.from_record(SfdRecord('FONDName:', data))
    font = SfdFont(metadata=SfdMetadata(records=[SfdRecord('FONDName:', data)]))
    with pytest.raises(SfdValidationError):
        font.validate()


def test_plain_text_is_not_utf7_or_postscript_interpreted():
    for data in (b'+AEI-', b'"literal quotes"', b'[userdict /key get]', b'not an integer array'):
        value = SfdFontText.from_record(SfdRecord('XUID:', data))
        assert value.text == data.decode('ascii')
        assert value.to_record().value == data
    assert SfdFontText.from_record(SfdRecord('FONDName:', b'legacy\xff')).text == 'legacyÿ'
    with pytest.raises(SfdParseError):
        SfdFontText.from_record(SfdRecord('Unknown:', b'text'))


@pytest.mark.parametrize('keyword', sorted(FONT_TEXT_KEYS))
def test_metadata_helpers_explicitly_write_back_and_preserve_order(keyword):
    before = SfdRecord('Before:', b'1')
    after = SfdRecord('After:', b'2')
    metadata = SfdMetadata(records=[before, SfdFontText(keyword, 'old').to_record(), after])
    value = metadata.find_text(keyword)
    value.text = 'new'
    assert metadata.find_text(keyword).text == 'old'
    metadata.set_text(value)
    assert metadata.find_text(keyword).text == 'new'
    assert metadata.records[0] is before
    assert metadata.records[2] is after
    assert len(metadata.records) == 3
    other = next(key for key in sorted(FONT_TEXT_KEYS) if key != keyword)
    assert metadata.find_text(other) is None
    metadata.set_text(SfdFontText(other, 'added'))
    assert metadata.records[-1] == SfdFontText(other, 'added').to_record()
    with pytest.raises(SfdValidationError):
        metadata.find_text('FontName:')
    original = metadata.records.copy()
    with pytest.raises(SfdValidationError):
        metadata.set_text(SfdFontText(keyword, 'bad\nvalue'))
    assert metadata.records == original


@pytest.mark.parametrize('keyword', sorted(FONT_TEXT_KEYS))
def test_duplicate_text_records_are_preserved_but_helpers_reject_ambiguity(keyword):
    font = SfdFont(
        metadata=SfdMetadata(
            records=[
                SfdFontText(keyword, 'first').to_record(),
                SfdFontText(keyword, 'second').to_record(),
            ]
        )
    )
    assert SfdFont.parse(font.dump_to_bytes()) == font
    before = font.metadata.records.copy()
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.metadata.find_text(keyword)
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.metadata.set_text(SfdFontText(keyword, 'third'))
    assert font.metadata.records == before


@pytest.mark.parametrize('keyword', sorted(FONT_TEXT_KEYS))
@pytest.mark.parametrize('line_ending', [b'\n', b'\r\n'])
def test_font_text_parser_continuations_and_record_preservation(keyword, line_ending):
    header = keyword.encode() + b' literal\\\ntext\n'
    source = b'SplineFontDB: 3.2\n' + header + b'BeginChars: 0 0\nEndChars\nEndSplineFont\n'
    # Logical continuations use backslash + LF; physical record endings may be CRLF.
    if line_ending == b'\r\n':
        source = source.replace(b'\n', b'\r\n').replace(b'\\\r\n', b'\\\n')
    font = SfdFont.parse(source)
    assert font.metadata.find_text(keyword).text == 'literaltext'
    assert SfdFont.parse(font.dump_to_bytes()) == font


@pytest.mark.parametrize('keyword', sorted(FONT_TEXT_KEYS))
@pytest.mark.parametrize('scope', ['glyph', 'layer'])
def test_font_text_is_restricted_to_font_metadata(keyword, scope):
    layer = SfdLayer(1)
    glyph = SfdGlyph('A', 0, layers=[layer])
    font = SfdFont(glyphs=[glyph])
    (glyph.records if scope == 'glyph' else layer.records).append(SfdFontText(keyword, 'value').to_record())
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()


@pytest.mark.parametrize('keyword', sorted(FONT_TEXT_KEYS))
def test_text_edits_keep_geometry_protected_until_dependencies_are_removed(tmp_path, keyword):
    font = SfdFont(glyphs=[SfdGlyph('A', 0, layers=[SfdLayer(1, [SfdContour([SfdPoint(0, 0)])])])])
    font.metadata.set_text(SfdFontText(keyword, 'old'))
    font = SfdFont.parse(font.dump_to_bytes())
    font.metadata.set_text(SfdFontText(keyword, 'edited'))
    assert SfdFont.parse(font.dump_to_bytes()) == font
    font.glyphs[0].layers[0].contours[0].points[0].x = 20
    path = tmp_path.joinpath('keep.sfd')
    path.write_bytes(b'keep')
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.save(path)
    assert path.read_bytes() == b'keep'
    font.metadata.records.clear()
    assert SfdFont.parse(font.dump_to_bytes()) == font


def test_upstream_xuid_text_editing(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    assert font.metadata.find_text('XUID:').text == '[1021 655 56001077 4734436]'
    value = font.metadata.find_text('XUID:')
    value.text = '[1021 655 56001077 4734437]'
    font.metadata.set_text(value)
    assert SfdFont.parse(font.dump_to_bytes()) == font
