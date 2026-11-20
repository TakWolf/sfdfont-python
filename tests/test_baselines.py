import pytest

from sfdfont import (
    SfdBaselineExtent,
    SfdBaselines,
    SfdBaselineScript,
    SfdFont,
    SfdParseError,
    SfdRecord,
    SfdValidationError,
)


def baselines():
    return SfdBaselines(
        tags=['romn', 'ideo'],
        scripts=[
            SfdBaselineScript(
                'latn',
                0,
                [0, -120],
                [
                    SfdBaselineExtent(None, -200, 800),
                    SfdBaselineExtent('kern', -100, 700, 1),
                    SfdBaselineExtent('dflt', -180, 780),
                ],
            )
        ],
    )


def test_baseline_models_and_copies():
    value = baselines()
    assert SfdBaselines.from_record(value.to_record()) == value
    assert value.copy().scripts is value.scripts
    assert value.deepcopy().scripts[0] is not value.scripts[0]
    assert value.deepcopy() == value
    assert value.scripts[0].copy() == value.scripts[0].deepcopy() == value.scripts[0]
    assert value.scripts[0].extents[0].copy() == value.scripts[0].extents[0].deepcopy()
    tags = []
    assert SfdBaselines(tags=tags).tags is tags
    assert SfdBaselineScript().extents is not SfdBaselineScript().extents


def test_deep_baseline_extents_do_not_recurse():
    value = SfdBaselines(scripts=[SfdBaselineScript(extents=[SfdBaselineExtent(depth=i) for i in range(1500)])])
    assert SfdBaselines.from_record(value.to_record()) == value
    assert value.deepcopy() == value


@pytest.mark.parametrize('keyword', ['BaseHoriz:', 'BaseVert:'])
def test_empty_baseline_tables(keyword):
    value = SfdBaselines(keyword)
    assert SfdBaselines.from_record(value.to_record()) == value


@pytest.mark.parametrize(
    'data',
    [
        b"2 'romn' 'romn'",
        b"1 'romn'\nBaseScript: 'latn' 1 0",
        b"1 'romn'\nBaseScript: 'latn' 0",
        b"0\nBaseScript: 'latn' 0\nBaseScript: 'latn' 0",
        b"0\nBaseScript: 'latn' 0 }",
        b"0\nBaseScript: 'latn' 0 { -200 800",
        b"0\nBaseScript: 'latn' 0 { -32769 800 }",
        b'0\nInjected: 1',
    ],
)
def test_invalid_baseline_records(data):
    with pytest.raises(SfdParseError):
        SfdBaselines.from_record(SfdRecord('BaseHoriz:', data))


@pytest.mark.parametrize('change', ['depth', 'positions', 'default', 'tag', 'duplicate'])
def test_invalid_baseline_model_fields(change):
    value = baselines()
    if change == 'depth':
        value.scripts[0].extents[0].depth = 1
    elif change == 'positions':
        value.scripts[0].positions.pop()
    elif change == 'default':
        value.scripts[0].default_baseline = 2
    elif change == 'tag':
        value.tags[0] = 'short'
    else:
        value.tags[1] = value.tags[0]
    with pytest.raises(SfdValidationError):
        value.to_record()


def test_upstream_baseline_edits_preserve_bindings(assets_dir):
    value = baselines()
    source = assets_dir.joinpath('fontforge', 'Ambrosia.sfd').read_bytes()
    source = source.replace(b'BeginChars:', b'BaseHoriz: ' + value.to_record().value + b'\nBeginChars:', 1)
    font = SfdFont.parse(source)
    index = next(i for i, item in enumerate(font.metadata.records) if item.keyword == 'BaseHoriz:')
    value = SfdBaselines.from_record(font.metadata.records[index])
    value.scripts[0].positions[0] = 10
    value.scripts[0].default_baseline = 1
    value.scripts[0].extents[0].descent -= 1
    font.metadata.records[index] = value.to_record()
    assert SfdFont.parse(font.dump_to_bytes()) == font
    value.tags[0] = 'hang'
    font.metadata.records[index] = value.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.dump_to_bytes()


def test_baseline_validation_and_scope():
    font = SfdFont()
    font.metadata.records.extend([baselines().to_record(), baselines().to_record()])
    with pytest.raises(SfdValidationError, match='duplicate baseline'):
        font.validate()
    font.metadata.records = [SfdRecord('BaseHoriz:', b"1 'romn'\nBaseScript: 'latn' 2 0")]
    with pytest.raises(SfdValidationError):
        font.validate()
