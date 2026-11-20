import math

import pytest

from sfdfont import SfdFont, SfdFontRealMetric, SfdParseError, SfdRecord, SfdValidationError
from sfdfont._metrics import REAL_KEYS


@pytest.mark.parametrize('keyword', sorted(REAL_KEYS))
def test_real_metric_models_and_helpers(keyword):
    value = SfdFontRealMetric(keyword, -12.5)
    assert SfdFontRealMetric.from_record(value.to_record()) == value
    assert value.copy() == value.deepcopy() == value
    font = SfdFont()
    assert font.metadata.find_metric(keyword) is None
    font.metadata.set_metric(value)
    found = font.metadata.find_metric(keyword)
    assert found == value
    found.value = 1.25
    assert font.metadata.find_metric(keyword).value == -12.5
    font.metadata.set_metric(found)
    assert font.metadata.find_metric(keyword).value == 1.25


@pytest.mark.parametrize('data, value', [(b'-12,5', -12.5), (b'+.5e2', 50), (b'-.5E-2', -0.005), (b'1.', 1)])
def test_native_real_spellings(data, value):
    model = SfdFontRealMetric.from_record(SfdRecord('ItalicAngle:', data))
    assert model.value == value
    assert SfdFontRealMetric.from_record(model.to_record()) == model


def test_real_metric_precision_and_negative_zero():
    for value in [1 / 3, 5e-324, 1.7976931348623157e308]:
        model = SfdFontRealMetric(value=value)
        assert SfdFontRealMetric.from_record(model.to_record()).value == value
    result = SfdFontRealMetric.from_record(SfdFontRealMetric(value=-0.0).to_record())
    assert math.copysign(1, result.value) == -1


@pytest.mark.parametrize('data', [b'nan', b'inf', b'-inf', b'1e9999', b'1_000', b'1,2.3', b'1 2', b'--1', b'1' * 129])
def test_invalid_real_metric_records(data):
    with pytest.raises(SfdParseError):
        SfdFontRealMetric.from_record(SfdRecord('UnderlineWidth:', data))


@pytest.mark.parametrize('value', [float('inf'), float('nan'), True, '1.5', 10**1000, 10**100])
def test_invalid_real_metric_models(value):
    with pytest.raises(SfdValidationError):
        SfdFontRealMetric(value=value).to_record()


@pytest.mark.parametrize('name', ['BoxesAndBounds.sfd', 'Ambrosia.sfd', 'NimbusLGCUni-Regular.sfd'])
def test_upstream_real_metric_edit_preserves_raw_spelling(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    originals = [item.deepcopy() for item in font.metadata.records if item.keyword in REAL_KEYS]
    for item in originals:
        value = SfdFontRealMetric.from_record(item)
        assert SfdFontRealMetric.from_record(value.to_record()) == value
    source = font.dump_to_bytes()
    parsed = SfdFont.parse(source)
    for item in originals:
        assert item in parsed.metadata.records
    font.metadata.set_metric(SfdFontRealMetric('ItalicAngle:', -12.5))
    assert SfdFont.parse(font.dump_to_bytes()) == font


def test_duplicate_real_metric_rejected():
    font = SfdFont()
    item = SfdFontRealMetric().to_record()
    font.metadata.records = [item, item.copy()]
    with pytest.raises(SfdValidationError, match='duplicate'):
        font.validate()
    with pytest.raises(SfdParseError):
        SfdFontRealMetric.from_record(SfdRecord('Unknown:', b'1.25'))
