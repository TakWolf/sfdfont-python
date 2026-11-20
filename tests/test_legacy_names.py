import pytest

from sfdfont import SfdFont, SfdGlyph, SfdLanguageNames, SfdParseError, SfdRecord, SfdStyleMapName, SfdValidationError
from sfdfont._legacy_names import LEGACY_NAME_KEYS
from sfdfont._strings import quote


@pytest.mark.parametrize('keyword', sorted(LEGACY_NAME_KEYS))
def test_style_mapping_name_models(keyword):
    value = SfdStyleMapName(keyword, '旧式名称 😀')
    assert SfdStyleMapName.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value


@pytest.mark.parametrize('data', [b'"unterminated', b'"ok" extra', b'"+A-"'])
def test_invalid_style_mapping_name_records(data):
    with pytest.raises(SfdParseError):
        SfdStyleMapName.from_record(SfdRecord('OS2StyleName:', data))


@pytest.mark.parametrize(
    'value',
    [
        SfdStyleMapName('Unknown:'),
        SfdStyleMapName(name=b'name'),
        SfdStyleMapName(name='\0'),
        SfdStyleMapName(name='\ud800'),
    ],
)
def test_invalid_style_mapping_name_models(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


def test_language_name_prefix_container_semantics():
    prefixes = [SfdStyleMapName('StyleMapFamilyName:', 'Legacy Family')]
    value = SfdLanguageNames(1033, [], prefixes)
    assert value.style_map_family_names is prefixes
    assert value.copy().style_map_family_names is prefixes
    assert value.deepcopy().style_map_family_names is not prefixes
    assert value.deepcopy() == value
    assert SfdLanguageNames(1033).style_map_family_names is not SfdLanguageNames(1033).style_map_family_names


def test_prefix_order_and_trailing_record_order_are_preserved(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    data = (
        b'StyleMapFamilyName: "First"\nStyleMapFamilyName: "Second"\nLangName: 1033\n'
        b'StyleMapFamilyName: "Trailing one"\nCustomBefore: 1\n'
        b'StyleMapFamilyName: "Trailing two"\nCustomAfter: 2\n'
    )
    font = SfdFont.parse(source.replace(b'LangName: 1033\n', data, 1))
    names = font.metadata.language_names[0]
    assert [item.name for item in names.style_map_family_names] == ['First', 'Second']
    assert names.names == []
    encoded = font.dump_to_bytes()
    assert encoded.index(b'StyleMapFamilyName: "First"') < encoded.index(b'StyleMapFamilyName: "Second"')
    assert encoded.index(b'StyleMapFamilyName: "Second"') < encoded.index(b'LangName: 1033')
    assert encoded.index(b'LangName: 1033') < encoded.index(b'StyleMapFamilyName: "Trailing one"')
    assert encoded.index(b'StyleMapFamilyName: "Trailing one"') < encoded.index(b'CustomBefore: 1')
    assert encoded.index(b'CustomBefore: 1') < encoded.index(b'StyleMapFamilyName: "Trailing two"')
    assert encoded.index(b'StyleMapFamilyName: "Trailing two"') < encoded.index(b'CustomAfter: 2')
    assert SfdFont.parse(encoded) == font
    names.style_map_family_names[0].name = '新名称 😀'
    assert SfdFont.parse(font.dump_to_bytes()) == font


def test_style_name_does_not_apply_stylemap_fallback(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    data = b'StyleMap: 0x0040\nOS2StyleName: "bold"\nOS2StyleName: "italic"\n'
    font = SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))
    assert font.metadata.find_metric('StyleMap:').value == 0x40
    names = [
        SfdStyleMapName.from_record(item).name for item in font.metadata.records if item.keyword == 'OS2StyleName:'
    ]
    assert names == ['bold', 'italic']
    assert SfdFont.parse(font.dump_to_bytes()) == font


def test_legacy_name_scope_and_invalid_prefix():
    item = SfdStyleMapName().to_record()
    font = SfdFont(glyphs=[SfdGlyph(records=[item])])
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()
    font = SfdFont()
    font.metadata.language_names = [SfdLanguageNames(1033, style_map_family_names=['\0'])]
    with pytest.raises(SfdValidationError, match='prefix'):
        font.validate()


def test_many_pending_family_names_retain_order(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    records = b''.join(b'StyleMapFamilyName: ' + quote(str(index)) + b'\nCustom: 1\n' for index in range(500))
    font = SfdFont.parse(source.replace(b'BeginChars:', records + b'BeginChars:', 1))
    names = [
        SfdStyleMapName.from_record(item).name
        for item in font.metadata.records
        if item.keyword == 'StyleMapFamilyName:'
    ]
    assert names == [str(index) for index in range(500)]
    assert SfdFont.parse(font.dump_to_bytes()) == font


@pytest.mark.parametrize('keyword', sorted(LEGACY_NAME_KEYS))
def test_plain_legacy_names_retain_their_form(keyword):
    value = SfdStyleMapName(keyword, 'Legacy Family 中文', False)
    assert SfdStyleMapName.from_record(value.to_record()) == value
    assert not value.to_record().value.startswith(b'"')


@pytest.mark.parametrize('text', [' leading', 'trailing ', 'line\nbreak', 'ending\\', '"ambiguous'])
def test_unrepresentable_plain_legacy_names(text):
    with pytest.raises(SfdValidationError):
        SfdStyleMapName(name=text, quoted=False).to_record()


def test_plain_name_nul_and_wrong_prefix_kind_rejected():
    with pytest.raises(SfdParseError):
        SfdStyleMapName.from_record(SfdRecord('OS2StyleName:', b'bad\0name'))
    font = SfdFont()
    font.metadata.language_names = [SfdLanguageNames(1033, style_map_family_names=[SfdStyleMapName()])]
    with pytest.raises(SfdValidationError, match='prefix'):
        font.validate()


def test_plain_and_quoted_prefixes_remain_distinct(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    source = source.replace(
        b'LangName: 1033\n',
        b'StyleMapFamilyName: Plain Family\nStyleMapFamilyName: "Quoted Family"\nLangName: 1033\n',
        1,
    )
    font = SfdFont.parse(source)
    prefixes = font.metadata.language_names[0].style_map_family_names
    assert [value.quoted for value in prefixes] == [False, True]
    assert SfdFont.parse(font.dump_to_bytes()) == font
