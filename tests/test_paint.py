import pytest

from sfdfont import SfdFont, SfdPaint, SfdParseError, SfdValidationError
from sfdfont._paint import decode_paint, encode_paint


def test_paint_header():
    data = b'2 1 1 0 #123456 .25 #fffffffe -1 10 round square [1 0 0 2] [3 4]'
    index, paint = decode_paint(data)
    assert index == 2
    assert paint.fill_color == 0x123456
    assert paint.fill_opacity == 0.25
    assert paint.stroke_opacity == -1
    assert paint.dash == (3, 4)
    assert decode_paint(encode_paint(index, paint)) == (index, paint)
    assert paint.copy() == paint.deepcopy() == paint


@pytest.mark.parametrize(
    'data',
    [
        b'1 0 0 1 #0 1 #0 1 10 unknown round [1 0 0 1] []',
        b'1 0 0 1 #0 1 #0 1 10 round round [1 0 0] []',
        b'1 0 3 1 #0 1 #0 1 10 round round [1 0 0 1] []',
        b'1 0 0 1 #g 1 #0 1 10 round round [1 0 0 1] []',
    ],
)
def test_invalid_paint_header(data):
    with pytest.raises(SfdParseError):
        decode_paint(data)


@pytest.mark.parametrize('changes', [{'fill_opacity': 1.1}, {'stroke_width': -2}, {'fill': 3}])
def test_invalid_paint_values(changes):
    paint = SfdPaint(**changes)
    with pytest.raises(SfdValidationError):
        encode_paint(1, paint)


def test_edit_datauri_paint_preserves_image(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'DataURI.sfd'))
    assert font.multilayer
    glyph = font.glyphs[0]
    assert glyph.layer_count == 3
    assert [layer.index for layer in glyph.layers] == [1, 2]
    layer = glyph.layers[1]
    image = layer.images[0].deepcopy()
    layer.paint.fill_color = 0xFF0000
    layer.paint.fill_opacity = 0.5
    path = tmp_path.joinpath('DataURI.sfd')
    font.save(path)
    saved = SfdFont.load(path)
    assert saved == font
    assert saved.glyphs[0].layers[1].images == [image]
    layer.paint = None
    with pytest.raises(SfdValidationError, match='paint'):
        font.dump_to_bytes()


def test_inherited_join_cap_and_dash_use_native_spellings():
    _, paint = decode_paint(b'1 1 0 1 #fffffffe -1 #fffffffe -1 -1 inher inher [1 0 0 1] [0 255]')
    assert paint.line_join == paint.line_cap == 'inherited'
    assert b'inher inher' in encode_paint(1, paint)


def test_gradient_and_pattern_grammar():
    from sfdfont._paint import decode_gradient, decode_pattern, encode_gradient, encode_pattern

    gradient = decode_gradient(b'220;260 490;450 0 pad 2 {0 #808080 1} {1 #000000 .5}')
    assert gradient.start == (220, 260)
    assert len(gradient.stops) == 2
    assert decode_gradient(encode_gradient(gradient)) == gradient
    pattern = decode_pattern(b'E 200;200 [1 0 0 1 0 0]')
    assert pattern.glyph == 'E'
    assert decode_pattern(encode_pattern(pattern)) == pattern
    paint = SfdPaint(fill_gradient=gradient, stroke_pattern=pattern)
    assert paint.copy() == paint.deepcopy() == paint
    assert paint.copy().fill_gradient is gradient
    assert paint.deepcopy().fill_gradient is not gradient
    with pytest.raises(SfdParseError, match='stop count'):
        decode_gradient(b'220;260 490;450 0 pad 3 {0 #808080 1} {1 #000000 .5}')
    with pytest.raises(SfdValidationError, match='singular'):
        pattern.transform = (1, 1, 1, 1, 0, 0)
        encode_pattern(pattern)


def test_edit_upstream_gradient_preserves_images(assets_dir, tmp_path):
    from sfdfont import SfdGradient, SfdGradientStop

    font = SfdFont.load(assets_dir.joinpath('fontforge', 'DataURI.sfd'))
    gradient = SfdGradient(stops=[SfdGradientStop(0, 0xFFFFFF), SfdGradientStop(1, 0)])
    font.glyphs[0].layers[0].paint.fill_gradient = gradient
    path = tmp_path.joinpath('DataURI.sfd')
    font.save(path)
    assert SfdFont.load(path) == font


def test_pattern_dependencies_and_combined_reference_cycles():
    from sfdfont import SfdGlyph, SfdLayer, SfdPattern, SfdReference

    first = SfdGlyph('A', layers=[SfdLayer(1, paint=SfdPaint(fill_pattern=SfdPattern('tile')))])
    second = SfdGlyph('tile', 1, layers=[SfdLayer(2, paint=SfdPaint())])
    font = SfdFont(multilayer=True, glyphs=[first, second])
    font.validate()
    second.layers[0].references.append(SfdReference(0))
    with pytest.raises(SfdValidationError, match='cyclic'):
        font.validate()
    second.layers[0].references.clear()
    first.layers[0].paint.fill_pattern.glyph = 'missing'
    with pytest.raises(SfdValidationError, match='dangling pattern'):
        font.validate()


def test_native_type3_background_paint():
    from sfdfont._parser import glyph
    from sfdfont._reader import Reader

    reader = Reader(
        b'A\nEncoding: 65 65 0\nWidth: 600\nLayerCount: 2\n'
        b'Layer: 0 0 0 0 #000000 0 #000000 0 0 inher inher [0 0 0 0] []\n'
        b'Layer: 1 1 0 1 #fffffffe 1 #fffffffe 1 -1 inher inher [1 0 0 1] []\nEndChar\n'
    )
    font = SfdFont(multilayer=True)
    font.glyphs.append(glyph(reader, font))
    font.validate()
    assert font.glyphs[0].layers[0].paint.fill is False
    assert b'Layer: 0 0 0 0' in font.dump_to_bytes()
