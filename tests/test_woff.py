import pytest

from sfdfont import SfdFont, SfdFontMetric, SfdGlyph, SfdParseError, SfdRecord, SfdValidationError, SfdWoffMetadata
from sfdfont._parser import record
from sfdfont._reader import Reader


@pytest.mark.parametrize(
    'text', ['', '  <metadata version="1.0">中文 😀</metadata>  ', '<not-xml', 'line one\nline two']
)
def test_woff_metadata_preserves_text_without_xml_parsing(text):
    value = SfdWoffMetadata(text)
    assert SfdWoffMetadata.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value


@pytest.mark.parametrize('value', [SfdWoffMetadata('a\0b'), SfdWoffMetadata('\ud800'), SfdWoffMetadata(b'<xml/>')])
def test_invalid_woff_metadata_model(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


@pytest.mark.parametrize('data', [b'not-quoted', b'"unterminated', b'"ok" extra', b'"+A-"'])
def test_malformed_woff_metadata(data):
    reader = Reader(b'woffMetadata: ' + data + b'\n')
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


@pytest.mark.parametrize('keyword', ['woffMajor:', 'woffMinor:'])
def test_woff_version_component_preserves_native_storage_and_sentinel(keyword):
    for number in [-0x80000000, 0, 1, 0x4455, 65535, 0x7FFFFFFF]:
        value = SfdFontMetric(keyword, number)
        assert SfdFontMetric.from_record(value.to_record()) == value
    with pytest.raises(SfdValidationError):
        SfdFontMetric(keyword, 1 << 31).to_record()
    with pytest.raises(SfdParseError):
        SfdFontMetric.from_record(SfdRecord(keyword, b'2147483648'))


def test_woff_components_do_not_infer_or_clear_each_other():
    font = SfdFont()
    font.metadata.set_metric(SfdFontMetric('woffMinor:', 3))
    assert font.metadata.find_metric('woffMajor:') is None
    font.metadata.set_metric(SfdFontMetric('woffMajor:', 0x4455))
    assert font.metadata.find_metric('woffMinor:').value == 3


def test_upstream_woff_edits_preserve_font_dependencies(assets_dir):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    value = SfdWoffMetadata('<metadata version="1.0">中文</metadata>')
    font.metadata.records.append(value.to_record())
    font.metadata.set_metric(SfdFontMetric('woffMajor:', 1))
    font.metadata.set_metric(SfdFontMetric('woffMinor:', 2))
    font = SfdFont.parse(font.dump_to_bytes())
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'woffMetadata:')
    edited = SfdWoffMetadata.from_record(font.metadata.records[index])
    edited.text += '\n<!-- updated -->'
    font.metadata.records[index] = edited.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    font.glyphs[0].unicode = 65
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


def test_woff_metadata_scope_and_duplicate_check():
    item = SfdWoffMetadata().to_record()
    font = SfdFont()
    font.metadata.records = [item, item.copy()]
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.validate()
    font.metadata.records.clear()
    font.glyphs = [SfdGlyph(records=[item])]
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()
    with pytest.raises(SfdParseError):
        SfdWoffMetadata.from_record(SfdRecord('Unknown:', b'""'))
