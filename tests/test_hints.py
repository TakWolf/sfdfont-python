from copy import deepcopy

import pytest

from sfdfont import (
    SfdCounterMasks,
    SfdFont,
    SfdLimitError,
    SfdParseError,
    SfdReadLimits,
    SfdStemHint,
    SfdStemHints,
    SfdValidationError,
)
from sfdfont._hints import HINT_KEYS, decode
from sfdfont._parser import record, spline_set
from sfdfont._reader import Reader


@pytest.mark.parametrize(
    'data',
    [
        b'HStem: -20 20G<10 30 40 60> 700 -21G',
        b'VStem: 0 10<0 100> 100 20',
        b'DStem: 275 298 516 696 175 58 265 81',
        b'DStem2: 0 0 10 0 0.707107 0.707107<0 200>',
        b'CounterMasks: 2 80 0001',
        b'MinimumDistance: x19,-1 y0,2',
    ],
)
def test_hint_models(data):
    reader = Reader(data)
    item = record(reader, reader.word())
    value = decode(item, HINT_KEYS)
    assert decode(value.to_record(), HINT_KEYS) == value
    assert value.copy() == value.deepcopy() == value


def test_hint_model_container_semantics():
    hints = []
    model = SfdStemHints(hints=hints)
    assert model.hints is hints
    hints.append(SfdStemHint(instances=[(0, 100)]))
    assert model.copy().hints is hints
    assert model.deepcopy().hints[0] is not hints[0]
    assert SfdStemHint().instances is not SfdStemHint().instances
    with pytest.raises(SfdValidationError):
        SfdCounterMasks([b'\0' * 13]).to_record()


@pytest.mark.parametrize(
    'data',
    [
        b'HStem: 0',
        b'HStem: 0 10<0>',
        b'DStem2: 0 0 10 0 1',
        b'DStem: 0 0 1 1 2 2',
        b'CounterMasks: 2 00',
        b'CounterMasks: 1 001',
        b'MinimumDistance: z0,1',
        b'MinimumDistance: x-2,1',
    ],
)
def test_malformed_hint_records(data):
    reader = Reader(data)
    with pytest.raises(SfdParseError):
        record(reader, reader.word())


def test_point_mask_size_is_bounded_before_hex_decoding():
    reader = Reader(b'0 0 m 0x' + b'ff' * 13 + b'\nEndSplineSet\n')
    with pytest.raises(SfdParseError, match='96 bits'):
        spline_set(reader)


def test_cumulative_hint_budget_includes_instances():
    reader = Reader(b'HStem: 0 10<0 100>\nVStem: 0 10\n', SfdReadLimits(max_hints=2))
    record(reader, reader.word())
    assert reader.hint_count == 2
    with pytest.raises(SfdLimitError, match='max_hints'):
        record(reader, reader.word())
    limits = SfdReadLimits(max_hints=2)
    assert limits == limits.__copy__() == deepcopy(limits)
    assert hash(limits) == hash(deepcopy(limits))
    assert limits != SfdReadLimits(max_hints=3)


@pytest.mark.parametrize('value', [-1, False, 1.5, '4'])
def test_invalid_hint_budget(value):
    with pytest.raises(ValueError, match='max_hints'):
        SfdReadLimits(max_hints=value)


@pytest.mark.parametrize('name', ['Ambrosia.sfd', 'Hinting.sfd', 'NimbusLGCUni-Regular.sfd'])
def test_upstream_hint_models(assets_dir, name):
    font = SfdFont.load(assets_dir.joinpath('fontforge', name))
    count = 0
    for glyph in font.glyphs:
        for group in [glyph.records, *(layer.records for layer in glyph.layers)]:
            for item in group:
                if item.keyword in HINT_KEYS:
                    value = decode(item, HINT_KEYS)
                    assert decode(value.to_record(), HINT_KEYS) == value
                    count += 1
    assert count


def test_edit_upstream_hint_values_and_preserve_count(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'Ambrosia.sfd'))
    groups = [*(g.records for g in font.glyphs), *(layer.records for g in font.glyphs for layer in g.layers)]
    group, index = next((g, i) for g in groups for i, item in enumerate(g) if item.keyword == 'HStem:' and item.value)
    hints = SfdStemHints.from_record(group[index])
    hints.hints[0].start += 1
    group[index] = hints.to_record()
    path = tmp_path.joinpath('Ambrosia.sfd')
    font.save(path)
    assert SfdFont.load(path) == font
    hints.hints.append(SfdStemHint(800, 20))
    group[index] = hints.to_record()
    with pytest.raises(SfdValidationError, match='uninterpreted'):
        font.save(path)


def test_glyph_hints_cannot_be_font_metadata():
    font = SfdFont()
    font.metadata.records.append(SfdStemHints().to_record())
    with pytest.raises(SfdValidationError, match='font metadata'):
        font.validate()
