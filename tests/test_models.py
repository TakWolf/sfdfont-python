from copy import copy, deepcopy

import pytest

from sfdfont import SfdContour, SfdFont, SfdGlyph, SfdLayer, SfdMetadata, SfdReadLimits


@pytest.mark.parametrize(
    ('factory', 'attribute'),
    [
        (SfdFont, 'glyphs'),
        (SfdFont, 'encoding_aliases'),
        (SfdFont, 'layer_infos'),
        (SfdMetadata, 'records'),
        (SfdGlyph, 'alternate_unicodes'),
        (SfdLayer, 'contours'),
        (SfdContour, 'points'),
    ],
)
def test_default_containers_are_independent(factory, attribute):
    first = factory()
    second = factory()
    assert getattr(first, attribute) is not getattr(second, attribute)
    assert SfdFont().metadata is not SfdFont().metadata


def test_constructor_preserves_supplied_empty_list():
    glyphs = []
    font = SfdFont(glyphs=glyphs)
    glyphs.append(SfdGlyph())
    assert font.glyphs is glyphs
    assert len(font.glyphs) == 1


def test_copy_and_deepcopy_preserve_sharing_and_isolate_mutations():
    layer = SfdLayer()
    font = SfdFont(glyphs=[SfdGlyph('A', layers=[layer]), SfdGlyph('B', layers=[layer])])
    shallow = font.copy()
    deep = font.deepcopy()
    assert shallow == deep == font
    assert shallow.glyphs is font.glyphs
    assert deep.glyphs is not font.glyphs
    assert deep.metadata is not font.metadata
    assert deep.layer_infos[0] is not font.layer_infos[0]
    assert deep.glyphs[0].layers[0] is deep.glyphs[1].layers[0]
    assert deep.glyphs[0].layers[0] is not layer
    deep.glyphs[0].width += 1
    assert deep != font
    assert font.glyphs[0].width == 1000


def test_font_snapshot_does_not_affect_equality_or_repr():
    font = SfdFont()
    original = font.deepcopy()
    original_repr = repr(font)
    font._snapshot = original
    assert font == original
    assert repr(font) == original_repr
    assert font.copy()._snapshot is original
    assert font.deepcopy()._snapshot is not original


@pytest.mark.parametrize('value', [-1, True, 1.5, '10'])
def test_read_limits_reject_invalid_values(value):
    with pytest.raises(ValueError):
        SfdReadLimits(max_bytes=value)


def test_read_limits_remain_immutable_and_hashable():
    limits = SfdReadLimits(max_bytes=100)
    assert limits == copy(limits) == deepcopy(limits)
    assert hash(limits) == hash(copy(limits))
    with pytest.raises(AttributeError):
        limits.max_bytes = 200
    with pytest.raises(AttributeError):
        del limits.max_bytes
