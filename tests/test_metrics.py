import pytest

from sfdfont import SfdFont, SfdFontMetric, SfdMetadata, SfdParseError, SfdRecord, SfdValidationError
from sfdfont._metrics import SCALAR_KEYS


@pytest.mark.parametrize('keyword', sorted(SCALAR_KEYS))
def test_all_scalar_metric_keywords(keyword):
    value = SfdFontMetric(keyword, 0)
    assert SfdFontMetric.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value


@pytest.mark.parametrize(
    'keyword, data, expected',
    [
        ('StyleMap:', b'0x0040', 0x40),
        ('StyleMap:', b'#0040', 0x40),
        ('StyleMap:', b'0x8000', -32768),
        ('StyleMap:', b'0xffff8000', -32768),
        ('StyleMap:', b'ffffffff', -1),
        ('FSType:', b'65535', -1),
        ('PfmFamily:', b'-1', 255),
        ('OS2WinAscent:', b'65535', -1),
    ],
)
def test_metric_native_integer_storage(keyword, data, expected):
    value = SfdFontMetric.from_record(SfdRecord(keyword, data))
    assert value.value == expected
    assert SfdFontMetric.from_record(value.to_record()) == value


@pytest.mark.parametrize(
    'keyword, data',
    [
        ('TTFWeight:', b'65536'),
        ('PfmFamily:', b'256'),
        ('PfmFamily:', b'-129'),
        ('OS2_UseTypoMetrics:', b'2'),
        ('OS2TypoAOffset:', b'-1'),
        ('StyleMap:', b'0x12340000'),
        ('StyleMap:', b'0x100000000'),
        ('StyleMap:', b'0x' + b'f' * 10000),
        ('TTFWidth:', b'5 6'),
    ],
)
def test_malformed_font_metric_records(keyword, data):
    with pytest.raises(SfdParseError):
        SfdFontMetric.from_record(SfdRecord(keyword, data))


@pytest.mark.parametrize(
    'value',
    [
        SfdFontMetric(value=True),
        SfdFontMetric(value=32768),
        SfdFontMetric('Unknown:', 0),
        SfdFontMetric('OS2WinDOffset:', 2),
    ],
)
def test_invalid_metric_models(value):
    with pytest.raises(SfdValidationError):
        value.to_record()


def test_metadata_metric_helpers_resolve_aliases_without_hidden_sync():
    other = SfdRecord('Custom:', b'keep')
    metadata = SfdMetadata(records=[other, SfdFontMetric('PfmWeight:', 400).to_record()])
    value = metadata.find_metric('TTFWeight:')
    assert value == SfdFontMetric('PfmWeight:', 400)
    value.value = 500
    assert metadata.find_metric('TTFWeight:').value == 400
    metadata.set_metric(value)
    assert metadata.find_metric('PfmWeight:').value == 500
    metadata.set_metric(SfdFontMetric('TTFWeight:', 600))
    assert metadata.records[0] is other
    assert len(metadata.records) == 2
    assert metadata.records[1].keyword == 'TTFWeight:'
    assert metadata.find_metric('HHeadAscent:') is None
    metadata.set_metric(SfdFontMetric('HHeadAscent:', 800))
    assert metadata.find_metric('HheadAscent:').value == 800
    with pytest.raises(SfdValidationError):
        metadata.find_metric('Unknown:')


def test_duplicate_metric_aliases_fail_without_mutating_metadata():
    metadata = SfdMetadata(
        records=[SfdFontMetric('TTFWeight:', 400).to_record(), SfdFontMetric('PfmWeight:', 500).to_record()]
    )
    before = metadata.deepcopy()
    with pytest.raises(SfdValidationError, match='duplicate'):
        metadata.find_metric('TTFWeight:')
    with pytest.raises(SfdValidationError, match='duplicate'):
        metadata.set_metric(SfdFontMetric('TTFWeight:', 600))
    assert metadata == before
    with pytest.raises(SfdValidationError, match='duplicate'):
        SfdFont(metadata=metadata).validate()


@pytest.mark.parametrize('name', ['BoxesAndBounds.sfd', 'NimbusLGCUni-Regular.sfd', 'DejaVuSerif.sfd'])
def test_upstream_metric_models_and_edits(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    for item in font.metadata.records:
        if item.keyword in SCALAR_KEYS:
            value = SfdFontMetric.from_record(item)
            assert SfdFontMetric.from_record(value.to_record()) == value
    font.metadata.set_metric(SfdFontMetric('TTFWeight:', 500))
    font.metadata.set_metric(SfdFontMetric('OS2TypoAscent:', 810))
    font.metadata.set_metric(SfdFontMetric('OS2TypoAOffset:', 0))
    assert SfdFont.parse(font.dump_to_bytes()) == font
