import pytest

from sfdfont import (
    SfdFont,
    SfdGlyph,
    SfdLegacyBinding,
    SfdLegacyPst,
    SfdParseError,
    SfdPositionValue,
    SfdRecord,
    SfdScriptLanguage,
    SfdScriptLanguages,
    SfdValidationError,
)
from sfdfont._parser import record
from sfdfont._reader import Reader


def test_script_language_models_and_container_ownership():
    languages = ['dflt', 'SRB ']
    entry = SfdScriptLanguage('cyrl', languages)
    lists = [[entry], []]
    table = SfdScriptLanguages(lists)
    assert entry.languages is languages
    assert entry.copy().languages is languages
    assert entry.deepcopy().languages is not languages
    assert table.lists is lists
    assert table.copy().lists is lists
    assert table.deepcopy().lists[0][0] is not entry
    assert table.deepcopy() == table
    assert SfdScriptLanguages.from_record(table.to_record()) == table
    assert SfdScriptLanguages.from_record(SfdScriptLanguages().to_record()) == SfdScriptLanguages()
    assert SfdScriptLanguages().lists is not SfdScriptLanguages().lists
    assert SfdScriptLanguage().languages is not SfdScriptLanguage().languages
    assert SfdScriptLanguage(languages=languages).languages is languages


def test_bare_padded_and_quoted_tags_preserve_final_space():
    reader = Reader(b"ScriptLang: 1\n 2 cyrl 1 SRB  'latn' 1 NLD \nNext: 1")
    item = record(reader, reader.word())
    assert item.value.endswith(b'NLD ')
    assert SfdScriptLanguages.from_record(item) == SfdScriptLanguages(
        [[SfdScriptLanguage('cyrl', ['SRB ']), SfdScriptLanguage('latn', ['NLD '])]]
    )
    assert reader.word() == 'Next:'


@pytest.mark.parametrize(
    'data',
    [
        b'-1',
        b'32768',
        b'1 -1',
        b'1 1 latn -1',
        b'1 1 latn 1',
        b'1 1 la 1 dflt',
        b'1 1 latn 1 SRB\n',
        b"1 1 'abc' 0",
        b'1 1 \xffabc 0',
        b'1 1 a\x00bc 0',
        b'0 trailing',
        b'1 0 trailing',
    ],
)
def test_invalid_script_language_records(data):
    with pytest.raises(SfdParseError):
        SfdScriptLanguages.from_record(SfdRecord('ScriptLang:', data))


@pytest.mark.parametrize('tag', ['lat', 'latin', 'a\nbc', '中文ab', '\x7fabc'])
def test_invalid_script_language_models(tag):
    with pytest.raises(SfdValidationError):
        SfdScriptLanguages([[SfdScriptLanguage(tag)]]).to_record()


@pytest.mark.parametrize('index', [0, 1, 0xFFFE, 0xFFFF])
def test_binding_indices_and_sentinels(index):
    value = SfdLegacyPst('Position:', SfdLegacyBinding(0, index, 'dist'), positions=[SfdPositionValue()])
    font = SfdFont(version='1.0', glyphs=[SfdGlyph(records=[value.to_record()])])
    # No explicit table: keep compatibility with pre-table historical records.
    font.validate()
    font.metadata.records.append(SfdScriptLanguages([[SfdScriptLanguage('latn', ['dflt'])]]).to_record())
    if index == 1:
        with pytest.raises(SfdValidationError, match='index outside'):
            font.validate()
    else:
        font.validate()


def test_script_language_table_version_scope_and_duplicate():
    item = SfdScriptLanguages().to_record()
    with pytest.raises(SfdValidationError, match='record in glyph'):
        SfdFont(version='1.0', glyphs=[SfdGlyph(records=[item])]).validate()
    font = SfdFont()
    font.metadata.records.append(item)
    with pytest.raises(SfdValidationError, match='version'):
        font.validate()
    font.version = '1.0'
    font.metadata.records.append(item)
    with pytest.raises(SfdValidationError, match='duplicate ScriptLang'):
        font.validate()


@pytest.mark.parametrize(
    'item, root',
    [
        (SfdRecord('KernsSLI:', b'65 -20 1'), False),
        (SfdRecord('AnchorClass:', b'"above" mark 0 1'), True),
        (SfdRecord('ContextPos:', b"coverage 0 1 'kern' 0 0 0 0\nEndFPST"), True),
        (SfdRecord('KernClass:', b'1 1 1 0\n0'), True),
    ],
)
def test_all_legacy_table_references_are_checked(item, root):
    font = SfdFont(version='1.0', glyphs=[SfdGlyph(encoding=65)])
    font.metadata.records.append(SfdScriptLanguages([[]]).to_record())
    (font.metadata.records if root else font.glyphs[0].records).append(item)
    with pytest.raises(SfdValidationError, match='index outside'):
        font.validate()


def test_ligature_caret_index_is_unused():
    font = SfdFont(version='1.0', glyphs=[SfdGlyph(records=[SfdRecord('LCarets:', b"0 42 '    ' 1 100")])])
    font.metadata.records.append(SfdScriptLanguages().to_record())
    font.validate()


@pytest.mark.parametrize('name', ['VKern.sfd', 'DejaVuSerif.sfd', 'NimbusLGCUni-Regular.sfd'])
def test_upstream_script_languages_normalize_and_protect_bindings(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'ScriptLang:')
    table = SfdScriptLanguages.from_record(font.metadata.records[index])
    assert table.lists
    font.metadata.records[index] = table.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    table.lists[0][0].languages.append('TRK ')
    font.metadata.records[index] = table.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()
