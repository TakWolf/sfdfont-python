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
