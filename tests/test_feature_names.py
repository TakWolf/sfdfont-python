import pytest

from sfdfont import (
    SfdCidInfo,
    SfdFeatureName,
    SfdFeatureNames,
    SfdFont,
    SfdGlyph,
    SfdParseError,
    SfdValidationError,
)
from sfdfont._parser import record
from sfdfont._reader import Reader


def test_stylistic_feature_names_and_copies():
    names = [SfdFeatureName(1033, 'Round a'), SfdFeatureName(2052, '圆形 a 😀')]
    value = SfdFeatureNames('ss01', names)
    assert value.names is names
    assert value.copy().names is names
    assert value.deepcopy().names[0] is not names[0]
    assert value.deepcopy() == value
    assert names[0].copy() == names[0].deepcopy() == names[0]
    assert SfdFeatureNames.from_record(value.to_record()) == value
    assert SfdFeatureNames().names is not SfdFeatureNames().names


def test_variant_names_empty_fields_parameters_and_trailer():
    parameters = []
    name = SfdFeatureName(1033, 'a style', '', '', parameters)
    value = SfdFeatureNames('cv01', [name], '')
    assert name.parameters is parameters
    assert SfdFeatureNames.from_record(value.to_record()) == value
    name.parameters.append('Single storey')
    value.names.append(SfdFeatureName(2052, 'a 的样式', '提示 😀', 'a', ['单层']))
    assert SfdFeatureNames.from_record(value.to_record()) == value
    assert value.deepcopy().names[0].parameters is not parameters
    value.trailer = None
    assert SfdFeatureNames.from_record(value.to_record()) == value


def test_legacy_simple_character_variant_names():
    value = SfdFeatureNames('cv01', [SfdFeatureName(1033, 'a style'), SfdFeatureName(2052, 'a 的样式')])
    assert SfdFeatureNames.from_record(value.to_record()) == value


@pytest.mark.parametrize(
    'data',
    [
        b"'ss01'",
        b"'ss01' 1033",
        b'\'ss01\' 1033 "A" 1033 "B"',
        b'\'ss01\' 65536 "A"',
        b'\'cv01\' 1033 "Name" "Tip"',
        b'\'cv01\' 1033 "Name" "Tip" "a" 2 "One"',
        b'\'cv01\' 1033 "Name" "Tip" "a" 32768',
        b'\'cv01\' 1033 "Name" "Tip" "a" -1',
        b'\'ss01\' 1033 "Name" "extra"',
        b'\'cv01\' 1033 "Name" "Tip" "a" 0 "" injected',
    ],
)
def test_malformed_feature_name_records(data):
    reader = Reader(b'OtfFeatName: ' + data + b'\n')
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


@pytest.mark.parametrize(
    'value',
    [
        SfdFeatureNames(),
        SfdFeatureNames('short', [SfdFeatureName()]),
        SfdFeatureNames('ss01', [SfdFeatureName(parameters=[])]),
        SfdFeatureNames('ss01', [SfdFeatureName()], trailer=''),
        SfdFeatureNames('cv01', [SfdFeatureName(tooltip='Tip')]),
        SfdFeatureNames('cv01', [SfdFeatureName(tooltip='', sample='', parameters=['a'] * 32768)]),
    ],
)
def test_invalid_feature_name_models(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


def test_upstream_feature_name_edits_and_binding_protection(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    value = SfdFeatureNames('cv01', [SfdFeatureName(1033, 'Name', 'Tip', 'a', ['One'])], '')
    item = value.to_record()
    data = b'OtfFeatName: ' + item.value + b'\n'
    font = SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'OtfFeatName:')
    value = SfdFeatureNames.from_record(font.metadata.records[index])
    value.names[0].tooltip = 'New tip'
    value.names[0].parameters[0] = 'New parameter'
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    value.tag = 'cv02'
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


def test_feature_name_duplicate_and_scope_validation():
    item = SfdFeatureNames('ss01', [SfdFeatureName(1033, 'Name')]).to_record()
    font = SfdFont()
    font.metadata.records = [item, SfdFeatureNames('ss02', [SfdFeatureName(1033, 'Other')]).to_record()]
    font.validate()
    font.metadata.records.append(item.copy())
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.validate()
    font.metadata.records.clear()
    font.glyphs = [SfdGlyph(records=[item])]
    with pytest.raises(SfdValidationError, match='record in glyph'):
        font.validate()
    font = SfdFont(cid=SfdCidInfo(), subfonts=[SfdFont()])
    font.subfonts[0].metadata.records.append(item)
    with pytest.raises(SfdValidationError, match='CID layout'):
        font.validate()


def test_nonempty_reserved_trailer_keeps_unicode_dependency_protected(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    item = SfdFeatureNames('cv01', [SfdFeatureName(1033, 'Name', '', '', [])], 'reserved').to_record()
    data = b'OtfFeatName: ' + item.value + b'\n'
    font = SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))
    font.glyphs[0].unicode = 65
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()
