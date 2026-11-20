import pytest

from sfdfont import (
    SfdFont,
    SfdMacFeature,
    SfdMacFeatures,
    SfdMacName,
    SfdMacSetting,
    SfdParseError,
    SfdRecord,
    SfdValidationError,
)


def mac_features():
    return SfdMacFeatures(
        [
            SfdMacFeature(
                1,
                True,
                0,
                [SfdMacName(data=b'Ligatures'), SfdMacName(0, 1, b'Ligatures FR')],
                [
                    SfdMacSetting(0, [SfdMacName(data=b'Off')]),
                    SfdMacSetting(1, [SfdMacName(data=b'On')]),
                ],
            ),
            SfdMacFeature(2, False, 255, [SfdMacName(data=b'')]),
        ]
    )


def test_mac_feature_models_and_copy_semantics():
    value = mac_features()
    assert SfdMacFeatures.from_record(value.to_record()) == value
    assert value.copy().features is value.features
    assert value.deepcopy().features[0].names[0] is not value.features[0].names[0]
    assert value.deepcopy() == value
    assert value.features[0].copy() == value.features[0].deepcopy() == value.features[0]
    assert value.features[0].settings[0].copy() == value.features[0].settings[0].deepcopy()
    features = []
    assert SfdMacFeatures(features).features is features
    assert SfdMacFeature().names is not SfdMacFeature().names
    assert 'Ligatures' in repr(value)


def test_mac_name_bytes_are_not_utf7():
    value = mac_features()
    value.features[0].names[0].data = b'\x8f"\\\n\x7f+-'
    item = value.to_record()
    assert b'\\217\\042\\134\\012\\177+-' in item.value
    assert SfdMacFeatures.from_record(item) == value


@pytest.mark.parametrize(
    'change',
    [
        'missing-feature-name',
        'missing-setting-name',
        'default',
        'feature',
        'mutex',
        'duplicate-feature',
        'duplicate-setting',
        'encoding',
        'language',
        'nul',
    ],
)
def test_invalid_mac_features_rejected(change):
    value = mac_features()
    feature = value.features[0]
    if change == 'missing-feature-name':
        feature.names.clear()
    elif change == 'missing-setting-name':
        feature.settings[0].names.clear()
    elif change == 'default':
        feature.default_setting = 256
    elif change == 'feature':
        feature.feature = 65536
    elif change == 'mutex':
        feature.is_mutex = 1
    elif change == 'duplicate-feature':
        value.features[1].feature = feature.feature
    elif change == 'duplicate-setting':
        feature.settings[1].setting = feature.settings[0].setting
    elif change == 'encoding':
        feature.names[0].encoding = 65536
    elif change == 'language':
        feature.names[0].language = -1
    else:
        feature.names[0].data = b'\0'
    with pytest.raises(SfdValidationError):
        value.to_record()


@pytest.mark.parametrize(
    'data',
    [
        b'1 1 0\nEndMacFeatures',
        b'1 1 0\nMacName: 0 0 1 "A"\nMacSetting: 0\nEndMacFeatures',
        b'1 1 256\nMacName: 0 0 1 "A"\nEndMacFeatures',
        b'1 1 0\nMacName: 0 0 2 "A"\nEndMacFeatures',
        b'1 1 0\nMacName: 0 0 1 "\\400"\nEndMacFeatures',
        b'1 1 0\nMacName: 0 0 1 "\\000"\nEndMacFeatures',
        b'1 1 0\nMacName: 65536 0 1 "A"\nEndMacFeatures',
        b'1 1 0\nMacName: 0 0 1 "A"\nEndMacFeatures\nInjected:',
        b'1 1 0\nMacName: 0 0 1 "A"',
    ],
)
def test_malformed_mac_feature_records(data):
    with pytest.raises(SfdParseError):
        SfdMacFeatures.from_record(SfdRecord('MacFeat:', data))


def test_empty_or_wrong_kind_mac_feature_table():
    with pytest.raises(SfdValidationError):
        SfdMacFeatures().to_record()
    with pytest.raises(SfdParseError):
        SfdMacFeatures.from_record(SfdRecord('Unknown:', mac_features().to_record().value))


def prepared_font(assets_dir):
    source = assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd').read_bytes()
    data = b'MacFeat: ' + mac_features().to_record().value + b'\n'
    return SfdFont.parse(source.replace(b'BeginChars:', data + b'BeginChars:', 1))


def test_mac_feature_edits_preserve_feature_and_name_bindings(assets_dir):
    font = prepared_font(assets_dir)
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'MacFeat:')
    value = SfdMacFeatures.from_record(font.metadata.records[index])
    value.features[0].default_setting = 1
    value.features[0].is_mutex = False
    value.features[0].names[0].data = b'Changed'
    value.features[0].settings[0].names[0].data = b'Disabled'
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    value.features[0].settings[0].setting = 2
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


def test_duplicate_mac_feature_tables(assets_dir):
    font = prepared_font(assets_dir)
    font.metadata.records.append(next(item for item in font.metadata.records if item.keyword == 'MacFeat:').copy())
    with pytest.raises(SfdValidationError, match='duplicate Mac feature table'):
        font.validate()
