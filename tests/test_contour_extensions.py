import pytest

from sfdfont import SfdFont, SfdLimitError, SfdParseError, SfdReadLimits, SfdSpiroPoint
from sfdfont._parser import spline_set
from sfdfont._reader import Reader


def test_named_points_contours_and_spiro():
    reader = Reader(
        b'0 0 m 0\nNamedP: "+Ti0A"\n10 20 l 0\nNamed: "outline"\n'
        b'PathFlags: 1\nPathStart: 2\nSpiro\n0 0 {\n10 20 }\n0 0 z\nEndSpiro\nEndSplineSet\n'
    )
    reader.point_count = 0
    contour = spline_set(reader)[0]
    assert contour.points[0].name == '中'
    assert contour.name == 'outline'
    assert contour.flags == 1
    assert contour.start_offset == 2
    assert contour.spiro == [SfdSpiroPoint(0, 0, '{'), SfdSpiroPoint(10, 20, '}'), SfdSpiroPoint(0, 0, 'z')]


@pytest.mark.parametrize(
    'data',
    [
        b'Named: "no preceding contour"\nEndSplineSet\n',
        b'0 0 m 0\nSpiro\n1 2 invalid\nEndSpiro\nEndSplineSet\n',
        b'0 0 m 0\nSpiro\n0 0 z\n',
    ],
)
def test_malformed_contour_extensions(data):
    reader = Reader(data)
    reader.point_count = 0
    with pytest.raises(SfdParseError):
        spline_set(reader)


def test_spiro_point_budget():
    reader = Reader(b'0 0 m 0\nSpiro\n0 0 z\nEndSpiro\nEndSplineSet\n', SfdReadLimits(max_points=1))
    reader.point_count = 0
    with pytest.raises(SfdLimitError):
        spline_set(reader)


def test_upstream_contour_attributes_after_explicitly_removing_opaque_records(assets_dir, tmp_path):
    font = SfdFont.load(assets_dir.joinpath('fontforge', 'BoxesAndBounds.sfd'))
    font.metadata.records.clear()
    for glyph in font.glyphs:
        glyph.records.clear()
        for layer in glyph.layers:
            layer.records.clear()
    contour = font.glyphs[0].layers[0].contours[0]
    contour.name = 'clip'
    contour.flags = 1
    contour.points[0].name = 'start😀'
    path = tmp_path.joinpath('BoxesAndBounds.sfd')
    font.save(path)
    assert SfdFont.load(path) == font
